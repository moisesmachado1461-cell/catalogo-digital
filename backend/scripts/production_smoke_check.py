"""Smoke test público, seguro e rápido do deploy de produção.

Uso mais simples (URLs oficiais do projeto):
    python scripts/production_smoke_check.py

Também aceita URLs alternativas:
    python scripts/production_smoke_check.py --api https://api.exemplo.com --frontend https://site.exemplo.com

O script não pede senha e não altera dados.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.request import Request, urlopen

BACKEND = Path(__file__).resolve().parents[1]
DEFAULT_API = "https://catalogo-digital-api.onrender.com"
DEFAULT_FRONTEND = "https://catalogo-digital-v3zs.onrender.com"


def current_app_version() -> str:
    source = (BACKEND / "app" / "version.py").read_text(encoding="utf-8")
    for line in source.splitlines():
        if line.strip().startswith("APP_VERSION") and "=" in line:
            return line.split("=", 1)[1].strip().strip('"\'')
    raise RuntimeError("APP_VERSION não encontrada em backend/app/version.py")


def fetch(url: str, method: str = "GET", headers: dict[str, str] | None = None):
    req = Request(url, method=method, headers=headers or {})
    with urlopen(req, timeout=90) as response:
        body = response.read().decode("utf-8", errors="replace")
        return response.status, dict(response.headers.items()), body


def header_value(headers: dict[str, str], name: str) -> str | None:
    name = name.lower()
    return next((value for key, value in headers.items() if key.lower() == name), None)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", default=DEFAULT_API)
    parser.add_argument("--frontend", default=DEFAULT_FRONTEND)
    parser.add_argument("--origin", help="Origem HTTPS esperada no CORS; por padrão usa --frontend")
    parser.add_argument("--expected-version", default=current_app_version())
    parser.add_argument("--expected-storage", default="cloudinary")
    args = parser.parse_args()

    api = args.api.rstrip("/")
    frontend = args.frontend.rstrip("/") if args.frontend else None
    origin = args.origin or frontend
    failures: list[str] = []

    print(f"CATÁLOGO DIGITAL — SMOKE DE PRODUÇÃO · esperado {args.expected_version}")

    try:
        status, headers, body = fetch(f"{api}/api/health")
        data = json.loads(body)
        actual_version = data.get("version")
        print(f"[OK] health HTTP {status} — versão {actual_version}")

        if status != 200 or data.get("status") != "ok" or data.get("database") != "ok":
            failures.append("health/database")
        if data.get("environment") != "production":
            failures.append("environment")
            print(f"[ERRO] environment={data.get('environment')!r}; esperado 'production'")
        if actual_version != args.expected_version:
            failures.append("version")
            print(f"[ERRO] versão online {actual_version!r}; esperada {args.expected_version!r}")

        storage = data.get("storage") if isinstance(data.get("storage"), dict) else {}
        if storage.get("provider") != args.expected_storage:
            failures.append("storage/provider")
            print(f"[ERRO] storage provider={storage.get('provider')!r}; esperado {args.expected_storage!r}")
        if storage.get("configured") is not True or storage.get("persistent") is not True:
            failures.append("storage/persistence")
            print(f"[ERRO] storage não está persistente/configurado: {storage!r}")
        else:
            print(f"[OK] storage {storage.get('provider')} persistente e configurado")

        for header in ("x-content-type-options", "x-frame-options", "referrer-policy", "x-request-id"):
            if header_value(headers, header) is None:
                failures.append(f"header {header}")
        if header_value(headers, "strict-transport-security") is None:
            failures.append("header HSTS")
    except Exception as exc:
        print(f"[ERRO] health: {exc}")
        failures.append("health")

    if origin:
        try:
            _, headers, _ = fetch(
                f"{api}/api/auth/login",
                method="OPTIONS",
                headers={
                    "Origin": origin,
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "content-type",
                },
            )
            allow_origin = header_value(headers, "access-control-allow-origin")
            if allow_origin != origin:
                failures.append("CORS")
                print(f"[ERRO] CORS retornou {allow_origin!r}; esperado {origin!r}")
            else:
                print(f"[OK] CORS aceita a origem oficial: {origin}")
        except Exception as exc:
            print(f"[ERRO] CORS: {exc}")
            failures.append("CORS")

    if frontend:
        for page in ("/", "/loja.html", "/admin.html", "/super-admin.html", "/service-worker.js"):
            try:
                status, _, body = fetch(frontend + page)
                if status != 200 or not body.strip():
                    failures.append(f"frontend {page}")
                    print(f"[ERRO] frontend {page}: HTTP {status} ou resposta vazia")
                else:
                    print(f"[OK] frontend {page}")
            except Exception as exc:
                print(f"[ERRO] frontend {page}: {exc}")
                failures.append(f"frontend {page}")

    print()
    if failures:
        print("Falhas: " + ", ".join(failures))
        return 1
    print("Smoke de produção concluído sem falhas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
