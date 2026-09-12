"""Smoke test público e seguro do deploy.

Uso:
    python scripts/production_smoke_check.py \
      --api https://catalogo-digital-api.onrender.com \
      --frontend https://catalogo-digital-v3zs.onrender.com

Não pede senha e não altera dados.
"""
from __future__ import annotations

import argparse
import json
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def fetch(url: str, method: str = "GET", headers: dict[str, str] | None = None):
    req = Request(url, method=method, headers=headers or {})
    with urlopen(req, timeout=90) as response:
        body = response.read().decode("utf-8", errors="replace")
        return response.status, dict(response.headers.items()), body


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", required=True)
    parser.add_argument("--frontend")
    parser.add_argument("--origin", help="Origem HTTPS esperada no CORS; por padrão usa --frontend")
    args = parser.parse_args()
    api = args.api.rstrip("/")
    frontend = args.frontend.rstrip("/") if args.frontend else None
    origin = args.origin or frontend
    failures = []

    try:
        status, headers, body = fetch(f"{api}/api/health")
        data = json.loads(body)
        print(f"[OK] health HTTP {status} — versão {data.get('version')}")
        if status != 200 or data.get("database") != "ok":
            failures.append("health/database")
        for header in ("x-content-type-options", "x-frame-options", "referrer-policy", "x-request-id"):
            if not any(k.lower() == header for k in headers):
                failures.append(f"header {header}")
        if data.get("environment") == "production" and not any(k.lower() == "strict-transport-security" for k in headers):
            failures.append("header HSTS")
    except Exception as exc:
        print(f"[ERRO] health: {exc}")
        failures.append("health")

    if origin:
        try:
            status, headers, _ = fetch(
                f"{api}/api/auth/login",
                method="OPTIONS",
                headers={
                    "Origin": origin,
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "content-type",
                },
            )
            allow_origin = next((v for k, v in headers.items() if k.lower() == "access-control-allow-origin"), None)
            if allow_origin != origin:
                failures.append("CORS")
                print(f"[ERRO] CORS retornou {allow_origin!r}; esperado {origin!r}")
            else:
                print(f"[OK] CORS aceita somente a origem testada: {origin}")
        except Exception as exc:
            print(f"[ERRO] CORS: {exc}")
            failures.append("CORS")

    if frontend:
        for page in ("/", "/admin.html", "/super-admin.html", "/service-worker.js"):
            try:
                status, _, _ = fetch(frontend + page)
                if status != 200:
                    failures.append(f"frontend {page}")
                else:
                    print(f"[OK] frontend {page}")
            except Exception as exc:
                print(f"[ERRO] frontend {page}: {exc}")
                failures.append(f"frontend {page}")

    print()
    if failures:
        print("Falhas: " + ", ".join(failures))
        return 1
    print("Smoke test público concluído sem falhas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
