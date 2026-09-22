"""Regressão funcional segura da Fase 24.2.

Cria um banco SQLite temporário, aplica migrations, executa o seed e sobe a API
localmente em uma porta livre. Nenhum dado de produção é acessado ou alterado.

Execute a partir de backend:
    python scripts/phase24_2_functional_regression.py

O script valida, entre outros pontos:
- login e papéis;
- isolamento multi-tenant real entre Mercado e Loja Tech;
- bloqueio de acesso cruzado a produto;
- guardas Admin x Super Admin;
- catálogo público, serviços, reserva e locação;
- edição de loja pelo Super Admin;
- cupom de produto e bloqueio de produto de outra loja;
- cupom de plano criado pelo Super Admin e validado pelo Admin;
- assinatura e central de cobrança em modo leitura.
"""
from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from contextlib import closing
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BACKEND = Path(__file__).resolve().parents[1]


def current_app_version() -> str:
    source = (BACKEND / "app" / "version.py").read_text(encoding="utf-8")
    for line in source.splitlines():
        if line.strip().startswith("APP_VERSION") and "=" in line:
            return line.split("=", 1)[1].strip().strip('"\'')
    raise CheckError("APP_VERSION não encontrada em backend/app/version.py")

DEMO_USERS = {
    "super": ("superadmin@catalogodigital.dev", "SuperAdmin@2026"),
    "market": ("admin@mercadobompreco.com", "Admin@12345"),
    "tech": ("admin@lojatechdemo.com", "Admin@67890"),
    "barber": ("admin@barbeariacentral.com", "Admin@24680"),
    "electric": ("admin@eletricasoldemo.com", "Admin@13579"),
    "hotel": ("admin@pousadaserena.com", "Admin@11223"),
    "rental": ("admin@alugafacildemo.com", "Admin@44556"),
}


class CheckError(RuntimeError):
    pass


def free_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def request_json(
    base: str,
    path: str,
    *,
    method: str = "GET",
    token: str | None = None,
    body: dict[str, Any] | None = None,
    expected: int = 200,
    timeout: int = 30,
) -> Any:
    payload = None
    headers = {"Accept": "application/json"}
    if body is not None:
        payload = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = Request(base + path, data=payload, method=method, headers=headers)
    try:
        with urlopen(req, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
            status = response.status
    except HTTPError as exc:
        status = exc.code
        raw = exc.read().decode("utf-8", errors="replace")
    except URLError as exc:
        raise CheckError(f"Falha de rede em {method} {path}: {exc}") from exc

    try:
        data = json.loads(raw) if raw else None
    except json.JSONDecodeError:
        data = raw

    if status != expected:
        raise CheckError(
            f"{method} {path}: HTTP {status}, esperado {expected}. Resposta: {data!r}"
        )
    return data


def login(base: str, email: str, password: str) -> str:
    data = request_json(
        base,
        "/api/auth/login",
        method="POST",
        body={"email": email, "password": password},
    )
    token = data.get("access_token") if isinstance(data, dict) else None
    if not token:
        raise CheckError(f"Login não retornou token para {email}")
    return token


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CheckError(message)


def wait_api(base: str, process: subprocess.Popen[str], seconds: int = 45) -> None:
    deadline = time.time() + seconds
    last_error = None
    while time.time() < deadline:
        if process.poll() is not None:
            out, err = process.communicate(timeout=5)
            raise CheckError(
                "API local encerrou antes do teste.\n"
                f"STDOUT:\n{out[-4000:]}\nSTDERR:\n{err[-4000:]}"
            )
        try:
            data = request_json(base, "/api/health", timeout=3)
            if isinstance(data, dict) and data.get("database") == "ok":
                return
        except Exception as exc:  # API ainda iniciando
            last_error = exc
        time.sleep(0.5)
    raise CheckError(f"API local não respondeu a tempo: {last_error}")


def run_setup(env: dict[str, str]) -> None:
    commands = [
        [sys.executable, "-m", "alembic", "-c", "alembic.ini", "upgrade", "head"],
        [sys.executable, "seed.py"],
    ]
    for command in commands:
        result = subprocess.run(
            command,
            cwd=BACKEND,
            env=env,
            capture_output=True,
            text=True,
            timeout=180,
        )
        if result.returncode != 0:
            raise CheckError(
                f"Falha no preparo: {' '.join(command)}\n"
                f"STDOUT:\n{result.stdout[-6000:]}\nSTDERR:\n{result.stderr[-6000:]}"
            )


def main() -> int:
    checks: list[str] = []

    def ok(message: str) -> None:
        checks.append(message)
        print(f"[OK] {message}")

    with tempfile.TemporaryDirectory(prefix="catalogo-f24-2-") as temp_dir:
        temp = Path(temp_dir)
        db_path = temp / "regression.db"
        uploads = temp / "uploads"
        uploads.mkdir(parents=True, exist_ok=True)

        env = os.environ.copy()
        env.update(
            {
                "DATABASE_URL": f"sqlite:///{db_path.as_posix()}",
                "ENVIRONMENT": "development",
                "JWT_SECRET": "phase24-2-functional-regression-secret-123456789",
                "CORS_ORIGINS": "http://127.0.0.1:5500",
                "STORAGE_PROVIDER": "local",
                "UPLOAD_DIR": str(uploads),
                "SENTRY_DSN": "",
                # Evita que logs INFO encham o pipe do subprocesso no Windows durante
                # dezenas de requisições sequenciais da regressão e bloqueiem a API.
                "LOG_LEVEL": "WARNING",
                "PYTHONUNBUFFERED": "1",
            }
        )

        run_setup(env)
        ok("Migrations + seed aplicados em banco temporário")

        port = free_port()
        base = f"http://127.0.0.1:{port}"
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "app.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
                "--log-level",
                "warning",
            ],
            cwd=BACKEND,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        try:
            wait_api(base, process)
            health = request_json(base, "/api/health")
            require(health.get("database") == "ok", "Health não confirmou banco")
            expected_version = current_app_version()
            require(health.get("version") == expected_version, f"Health não está em {expected_version}")
            ok(f"API local iniciou com health {expected_version}")

            # Login / papéis / tenants
            tokens = {key: login(base, *credentials) for key, credentials in DEMO_USERS.items()}
            me_market = request_json(base, "/api/auth/me", token=tokens["market"])
            me_tech = request_json(base, "/api/auth/me", token=tokens["tech"])
            me_super = request_json(base, "/api/auth/me", token=tokens["super"])
            require(me_market["role"] == "ADMINISTRADOR_DA_LOJA", "Mercado sem papel Admin")
            require(me_tech["role"] == "ADMINISTRADOR_DA_LOJA", "Tech sem papel Admin")
            require(me_super["role"] == "SUPER_ADMINISTRADOR", "Super Admin com papel incorreto")
            require(me_market["store_id"] != me_tech["store_id"], "Duas contas apontam para a mesma loja")
            ok("Logins, papéis e vínculo de lojas estão coerentes")

            market_store = request_json(base, "/api/admin/store", token=tokens["market"])
            tech_store = request_json(base, "/api/admin/store", token=tokens["tech"])
            require(market_store["slug"] == "mercado-bom-preco", "Mercado recebeu outra loja")
            require(tech_store["slug"] == "loja-tech-demo", "Tech recebeu outra loja")
            ok("Admin recebe somente a própria loja")

            market_products = request_json(base, "/api/admin/products", token=tokens["market"])
            tech_products = request_json(base, "/api/admin/products", token=tokens["tech"])
            market_skus = {p.get("sku") for p in market_products}
            tech_skus = {p.get("sku") for p in tech_products}
            require("HORT-001" in market_skus, "Produto do Mercado não apareceu")
            require("TECH-001" not in market_skus, "Produto da Tech vazou para o Mercado")
            require("TECH-001" in tech_skus, "Produto da Tech não apareceu")
            require("HORT-001" not in tech_skus, "Produto do Mercado vazou para a Tech")
            ok("Listagem de produtos está isolada entre duas lojas")

            market_product = next(p for p in market_products if p.get("sku") == "HORT-001")
            tech_product = next(p for p in tech_products if p.get("sku") == "TECH-001")
            request_json(
                base,
                f"/api/admin/products/{market_product['id']}",
                token=tokens["tech"],
                expected=404,
            )
            request_json(
                base,
                f"/api/admin/products/{tech_product['id']}",
                token=tokens["market"],
                expected=404,
            )
            ok("Acesso direto cruzado a produto de outra loja é bloqueado")

            request_json(base, "/api/super-admin/stores", token=tokens["market"], expected=403)
            request_json(base, "/api/admin/products", token=tokens["super"], expected=403)
            ok("Guardas de papel Admin/Super Admin estão funcionando")

            # Público e modelos de negócio
            market_public = request_json(base, "/api/public/stores/mercado-bom-preco")
            tech_public = request_json(base, "/api/public/stores/loja-tech-demo")
            require(market_public["slug"] == "mercado-bom-preco", "Loja pública Mercado incorreta")
            require(tech_public["slug"] == "loja-tech-demo", "Loja pública Tech incorreta")

            market_catalog = request_json(base, "/api/public/stores/mercado-bom-preco/catalog")
            tech_catalog = request_json(base, "/api/public/stores/loja-tech-demo/catalog")
            require(
                any(p.get("sku") == "HORT-001" for p in market_catalog.get("products", [])),
                "Catálogo público do Mercado incompleto",
            )
            require(
                any(p.get("sku") == "TECH-001" for p in tech_catalog.get("products", [])),
                "Catálogo público da Tech incompleto",
            )
            ok("Catálogos públicos carregam dados da loja correta")

            # Portal do cliente e acompanhamento público de pedido
            guest_order = request_json(
                base,
                "/api/public/stores/mercado-bom-preco/orders",
                method="POST",
                expected=201,
                body={
                    "customer": {"name": "Cliente Portal Teste", "email": "cliente.portal.teste@example.com", "phone": "11999990000"},
                    "items": [{"product_id": market_product["id"], "quantity": 1, "selected_option_item_ids": []}],
                    "payment_method": "DINHEIRO",
                    "fulfillment_method": "RETIRADA",
                },
            )
            require(bool(guest_order.get("public_token")), "Pedido não retornou token público de acompanhamento")
            tracked_order = request_json(
                base,
                f"/api/public/stores/mercado-bom-preco/orders/{guest_order['public_token']}",
            )
            require(tracked_order.get("order_number") == guest_order.get("order_number"), "Acompanhamento público retornou outro pedido")
            require((tracked_order.get("customer") or {}).get("email") is None, "Acompanhamento público expôs e-mail do cliente")

            customer_registration = request_json(
                base,
                "/api/customer/register",
                method="POST",
                expected=201,
                body={
                    "store_slug": "mercado-bom-preco",
                    "name": "Cliente Portal Teste",
                    "email": "cliente.portal.teste@example.com",
                    "phone": "11999990000",
                    "password": "Cliente2026",
                    "tracking_type": "ORDER",
                    "tracking_token": guest_order["public_token"],
                },
            )
            customer_token = customer_registration.get("access_token")
            require(bool(customer_token), "Cadastro do cliente não retornou sessão")
            customer_me = request_json(base, "/api/customer/me", token=customer_token)
            require(customer_me.get("store", {}).get("slug") == "mercado-bom-preco", "Conta do cliente ficou vinculada à loja errada")
            customer_orders = request_json(base, "/api/customer/orders", token=customer_token)
            require(any(row.get("id") == guest_order.get("id") for row in customer_orders), "Pedido acompanhado não apareceu na conta do cliente")
            request_json(base, "/api/admin/products", token=customer_token, expected=401)
            ok("Login do cliente e acompanhamento de pedido funcionam sem acesso ao Admin")

            barber_public = request_json(base, "/api/public/stores/barbearia-central-demo/services")
            require(len(barber_public.get("services", [])) >= 1, "Barbearia sem serviços")
            require(len(barber_public.get("professionals", [])) >= 1, "Barbearia sem profissionais")
            hotel_public = request_json(base, "/api/public/stores/pousada-serena-demo/resources")
            rental_public = request_json(base, "/api/public/stores/aluga-facil-demo/rental-items")
            require(len(hotel_public.get("resources", [])) >= 1, "Pousada sem recursos")
            require(len(rental_public.get("items", [])) >= 1, "Locação sem itens")
            ok("Serviços, reservas e locações públicas continuam disponíveis")

            # Rotas Admin dos segmentos
            request_json(base, "/api/admin/services", token=tokens["barber"])
            request_json(base, "/api/admin/professionals", token=tokens["barber"])
            request_json(base, "/api/admin/quotes", token=tokens["electric"])
            request_json(base, "/api/admin/resources", token=tokens["hotel"])
            request_json(base, "/api/admin/rental-items", token=tokens["rental"])
            ok("Painéis Admin dos principais modelos respondem sem regressão")

            # Edição de loja pelo Super Admin, somente no banco temporário
            stores = request_json(base, "/api/super-admin/stores", token=tokens["super"])
            market_sa = next(s for s in stores if s.get("slug") == "mercado-bom-preco")
            update_payload = {
                "name": market_sa["name"],
                "slug": market_sa["slug"],
                "business_category_id": market_sa["business_category"]["id"],
                "description": "Teste automatizado Fase 24.2",
                "primary_color": market_sa.get("primary_color") or "#7C3AED",
                "secondary_color": market_sa.get("secondary_color") or "#4F46E5",
                "whatsapp": market_sa.get("whatsapp"),
                "phone": market_sa.get("phone"),
                "email": market_sa.get("email"),
                "address": market_sa.get("address"),
                "city": market_sa.get("city"),
                "state": market_sa.get("state"),
                "zip_code": market_sa.get("zip_code"),
                "admin_name": (market_sa.get("admin") or {}).get("name"),
                "admin_email": (market_sa.get("admin") or {}).get("email"),
            }
            updated_store = request_json(
                base,
                f"/api/super-admin/stores/{market_sa['id']}",
                method="PATCH",
                token=tokens["super"],
                body=update_payload,
            )
            require(updated_store.get("description") == "Teste automatizado Fase 24.2", "Edição de loja não persistiu")
            ok("Super Admin consegue editar loja")

            # Cupom de produto: criação, exposição pública e bloqueio cross-tenant
            coupon = request_json(
                base,
                "/api/admin/coupons",
                method="POST",
                token=tokens["market"],
                expected=201,
                body={
                    "code": "F24PROD10",
                    "description": "Teste de cupom por produto",
                    "discount_type": "PERCENT",
                    "value": 10,
                    "min_order_value": 0,
                    "max_discount": 20,
                    "usage_limit": 5,
                    "is_active": True,
                    "is_public": True,
                    "product_ids": [market_product["id"]],
                },
            )
            require(coupon.get("product_ids") == [market_product["id"]], "Cupom não ficou vinculado ao produto")
            public_coupons = request_json(base, "/api/public/stores/mercado-bom-preco/coupons")
            require(any(c.get("code") == "F24PROD10" for c in public_coupons), "Cupom público não apareceu")
            coupon_order = request_json(
                base,
                "/api/public/stores/mercado-bom-preco/orders",
                method="POST",
                expected=201,
                body={
                    "customer": {"name": "Cliente Cupom", "email": "cliente.cupom@example.com", "phone": "11988887777"},
                    "items": [{"product_id": market_product["id"], "quantity": 1, "selected_option_item_ids": []}],
                    "payment_method": "DINHEIRO",
                    "fulfillment_method": "RETIRADA",
                    "coupon_code": "F24PROD10",
                },
            )
            require(float(coupon_order.get("discount_amount") or 0) > 0, "Cupom não descontou o pedido")
            require(
                float((coupon_order.get("payment") or {}).get("amount") or -1) == float(coupon_order.get("total") or -2),
                "Pagamento não recebeu o total final com desconto",
            )
            request_json(
                base,
                "/api/admin/coupons",
                method="POST",
                token=tokens["tech"],
                expected=400,
                body={
                    "code": "INVALIDO",
                    "discount_type": "PERCENT",
                    "value": 10,
                    "is_active": True,
                    "is_public": False,
                    "product_ids": [market_product["id"]],
                },
            )
            ok("Cupom desconta pedido e pagamento, sem aceitar produto de outra loja")

            # Cupom de plano SaaS
            plans = request_json(base, "/api/plans")
            professional = next(p for p in plans if p.get("code") == "PROFISSIONAL")
            billing_coupon = request_json(
                base,
                "/api/super-admin/billing/coupons",
                method="POST",
                token=tokens["super"],
                expected=201,
                body={
                    "code": "F24PRO20",
                    "description": "Teste de cupom do plano Profissional",
                    "discount_type": "PERCENT",
                    "value": 20,
                    "duration": "FIRST_INVOICE",
                    "usage_limit": 10,
                    "is_active": True,
                    "plan_ids": [professional["id"]],
                },
            )
            require(billing_coupon.get("code") == "F24PRO20", "Super Admin não criou cupom de plano")
            validation = request_json(
                base,
                "/api/admin/billing/validate-coupon",
                method="POST",
                token=tokens["market"],
                body={
                    "plan_id": professional["id"],
                    "billing_cycle": "MONTHLY",
                    "coupon_code": "F24PRO20",
                },
            )
            require(validation.get("valid") is True, "Admin não conseguiu validar cupom do plano")
            require(float(validation.get("discount_amount") or 0) > 0, "Cupom de plano não calculou desconto")
            ok("Cupom de plano é criado pelo Super Admin e validado pelo Admin")

            # Cobrança / assinatura somente leitura
            request_json(base, "/api/admin/subscription", token=tokens["market"])
            request_json(base, "/api/admin/billing/overview", token=tokens["market"])
            request_json(base, "/api/super-admin/dashboard", token=tokens["super"])
            request_json(base, "/api/super-admin/billing/invoices", token=tokens["super"])
            ok("Assinatura, Meu Plano e Central de Cobrança respondem corretamente")

            request_json(base, "/api/public/stores/nao-existe", expected=404)
            ok("Loja inexistente retorna 404 sem vazar dados")

        finally:
            process.terminate()
            try:
                process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)

    print()
    print("CATÁLOGO DIGITAL — FASE 24.2")
    print(f"Resultado: {len(checks)} verificações funcionais OK, 0 erros.")
    print("Banco e servidor usados no teste eram temporários e já foram removidos.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except CheckError as exc:
        print(f"[ERRO] {exc}", file=sys.stderr)
        raise SystemExit(1)
