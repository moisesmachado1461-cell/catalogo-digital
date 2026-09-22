"""Auditoria integrada da Fase 24.4.

Valida os três principais frontends sem alterar banco nem depender de serviços externos:
- loja pública / cliente;
- painel Admin;
- painel Super Admin.

Execute a partir de backend:
    python scripts/phase24_4_integrated_review.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend"

errors: list[str] = []
warnings: list[str] = []
passes: list[str] = []


def ok(message: str) -> None:
    passes.append(message)


def fail(message: str) -> None:
    errors.append(message)


def warn(message: str) -> None:
    warnings.append(message)


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def current_app_version() -> str | None:
    source = text(ROOT / "backend" / "app" / "version.py")
    match = re.search(r'APP_VERSION\s*=\s*["\']([^"\']+)["\']', source)
    return match.group(1) if match else None


def check_required_surfaces() -> None:
    required = [
        FRONTEND / "loja.html",
        FRONTEND / "admin.html",
        FRONTEND / "super-admin.html",
        FRONTEND / "js" / "loja.js",
        FRONTEND / "js" / "admin.js",
        FRONTEND / "js" / "super-admin.js",
        FRONTEND / "js" / "api.js",
        FRONTEND / "js" / "shared" / "dom-utils.js",
        FRONTEND / "css" / "store-premium.css",
        FRONTEND / "css" / "admin-premium.css",
        FRONTEND / "css" / "super-admin-premium.css",
        FRONTEND / "css" / "design-system.css",
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
    if missing:
        fail("Superfícies obrigatórias ausentes: " + ", ".join(missing))
    else:
        ok("Cliente, Admin e Super Admin possuem HTML, JavaScript e CSS premium dedicados")


def check_html_foundations() -> None:
    issues: list[str] = []
    for name in ("loja.html", "admin.html", "super-admin.html"):
        page = text(FRONTEND / name)
        if 'lang="pt-BR"' not in page:
            issues.append(f"{name}: lang pt-BR ausente")
        if 'name="viewport"' not in page:
            issues.append(f"{name}: viewport ausente")
        if "<title>" not in page:
            issues.append(f"{name}: title ausente")
        for shared in ("css/style.css", "css/design-system.css"):
            if shared not in page:
                issues.append(f"{name}: {shared} ausente")
    if issues:
        fail("Fundação HTML inconsistente: " + "; ".join(issues))
    else:
        ok("As três áreas compartilham idioma, viewport, título e Design System base")


def check_premium_styles() -> None:
    pairs = {
        "loja.html": "css/store-premium.css",
        "admin.html": "css/admin-premium.css",
        "super-admin.html": "css/super-admin-premium.css",
    }
    missing = [f"{page} -> {css}" for page, css in pairs.items() if css not in text(FRONTEND / page)]
    if missing:
        fail("CSS premium não conectado: " + "; ".join(missing))
    else:
        ok("Cada área principal carrega sua camada visual premium")


def check_responsive_css() -> None:
    issues: list[str] = []
    for css_name in ("store-premium.css", "admin-premium.css", "super-admin-premium.css"):
        css = text(FRONTEND / "css" / css_name)
        media_count = len(re.findall(r"@media\s*\(", css))
        if media_count < 2:
            issues.append(f"{css_name}: apenas {media_count} breakpoint(s)")
    if issues:
        warn("Revisar cobertura responsiva: " + "; ".join(issues))
    else:
        ok("As três camadas premium possuem múltiplos breakpoints responsivos")


def referenced_ids(js: str) -> set[str]:
    ids = set(re.findall(r"(?:\$|\$s)\(['\"]#([A-Za-z0-9_-]+)['\"]\)", js))
    ids.update(re.findall(r"getElementById\(['\"]([A-Za-z0-9_-]+)['\"]\)", js))
    return ids


def declared_ids(source: str) -> set[str]:
    return set(re.findall(r"id=[\"']([^\"']+)[\"']", source))


def check_dom_integrity() -> None:
    pairs = [
        ("loja.js", "loja.html"),
        ("admin.js", "admin.html"),
        ("super-admin.js", "super-admin.html"),
    ]
    issues: list[str] = []
    for js_name, html_name in pairs:
        js = text(FRONTEND / "js" / js_name)
        html = text(FRONTEND / html_name)
        refs = referenced_ids(js)
        available = declared_ids(html) | declared_ids(js)  # modais/formulários podem ser montados dinamicamente
        missing = sorted(refs - available)
        if missing:
            issues.append(f"{js_name}: {', '.join(missing)}")
    if issues:
        fail("IDs usados pelo JavaScript sem elemento estático/dinâmico detectável: " + "; ".join(issues))
    else:
        ok("Referências DOM de Cliente, Admin e Super Admin possuem elementos correspondentes")


def check_auth_integration() -> None:
    api_js = text(FRONTEND / "js" / "api.js")
    admin_js = text(FRONTEND / "js" / "admin.js")
    super_js = text(FRONTEND / "js" / "super-admin.js")
    issues: list[str] = []
    required_api = [
        "sessionStorage.getItem('catalogo_token')",
        "sessionStorage.removeItem('catalogo_token')",
        "Authorization",
        "response.status === 401",
    ]
    for marker in required_api:
        if marker not in api_js:
            issues.append(f"api.js sem {marker}")
    if "me.role === 'SUPER_ADMINISTRADOR'" not in admin_js or "super-admin.html" not in admin_js:
        issues.append("Admin não redireciona Super Admin de forma detectável")
    if "superMe.role !== 'SUPER_ADMINISTRADOR'" not in super_js:
        issues.append("Super Admin não valida papel de forma detectável")
    if issues:
        fail("Integração de autenticação inconsistente: " + "; ".join(issues))
    else:
        ok("JWT usa sessão do navegador, limpa 401 e separa os papéis Admin/Super Admin")


def check_public_store_integration() -> None:
    loja_js = text(FRONTEND / "js" / "loja.js")
    required = [
        "/api/public/stores/${encodeURIComponent(slug)}",
        "store.capabilities",
        "loadPublicCoupons",
        "loadPaymentOptions",
        "appointments",
        "reservations",
        "rentals",
    ]
    missing = [marker for marker in required if marker not in loja_js]
    if missing:
        fail("Loja pública sem integração detectável para: " + ", ".join(missing))
    else:
        ok("Loja pública permanece capability-driven e integrada a catálogo/serviços/cupons/pagamentos")


def check_shared_frontend_runtime() -> None:
    issues: list[str] = []
    for name in ("loja.html", "admin.html", "super-admin.html"):
        page = text(FRONTEND / name)
        for script in ("js/runtime-config.js", "js/shared/dom-utils.js", "js/api.js", "js/ui-system.js", "js/pwa.js"):
            if script not in page:
                issues.append(f"{name}: {script}")
    if issues:
        fail("Runtime compartilhado incompleto: " + "; ".join(issues))
    else:
        ok("As três áreas usam runtime de API, UI compartilhada e PWA")


def check_assistant_expertise() -> None:
    knowledge_path = ROOT / "backend" / "app" / "assistant_knowledge.json"
    frontend_knowledge = text(FRONTEND / "js" / "assistant-knowledge.js")
    assistant_backend = text(ROOT / "backend" / "app" / "routes" / "assistant.py")
    assistant_frontend = text(FRONTEND / "js" / "assistant.js")
    try:
        knowledge = json.loads(text(knowledge_path))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"Base do assistente inválida: {exc}")
        return
    entries = knowledge.get("entries") or []
    entry_ids = {str(item.get("id")) for item in entries if isinstance(item, dict)}
    required = {
        "roles-and-permissions", "tenant-isolation", "store-public-link",
        "store-coupon-troubleshooting", "store-vs-billing-coupons",
        "billing-full-coupon", "simple-store-payments", "payment-status-flow",
        "marketplace-payments", "mercado-pago-credentials-error",
        "login-session-help", "deploy-cache-help", "assistant-security",
    }
    issues: list[str] = []
    missing = sorted(required - entry_ids)
    if missing:
        issues.append("tópicos ausentes: " + ", ".join(missing))
    if len(entries) < 50:
        issues.append(f"cobertura insuficiente: {len(entries)} tópicos")
    if str(knowledge.get("version")) not in frontend_knowledge:
        issues.append("base frontend não está sincronizada")
    for marker in ("SEMPRE em português do Brasil", "no máximo 3", "Não revele"):
        if marker not in assistant_backend:
            issues.append(f"regra backend ausente: {marker}")
    if "slice(0, 3)" not in assistant_frontend:
        issues.append("limite objetivo ausente no frontend")
    if issues:
        fail("Assistente especialista incompleto: " + "; ".join(issues))
    else:
        ok(f"Assistente especialista possui {len(entries)} tópicos, contexto, objetividade e proteção de segredos")


def check_phase_metadata() -> None:
    version = current_app_version()
    readme = text(ROOT / "README.md")
    status = text(ROOT / "docs" / "STATUS_ATUAL.md")
    issues: list[str] = []
    if not version:
        issues.append("APP_VERSION não encontrada")
    else:
        if version not in readme:
            issues.append(f"README não registra a versão {version}")
        if version not in status:
            issues.append(f"STATUS_ATUAL não registra a versão {version}")
    if issues:
        fail("Metadados da fase incompletos: " + "; ".join(issues))
    else:
        ok(f"Versão, README e status estão alinhados em {version}")


def main() -> int:
    checks = [
        check_required_surfaces,
        check_html_foundations,
        check_premium_styles,
        check_responsive_css,
        check_dom_integrity,
        check_auth_integration,
        check_public_store_integration,
        check_shared_frontend_runtime,
        check_assistant_expertise,
        check_phase_metadata,
    ]
    for check in checks:
        check()

    print(f"CATÁLOGO DIGITAL — REVISÃO INTEGRADA · VERSÃO {current_app_version() or 'desconhecida'}")
    for message in passes:
        print(f"[OK] {message}")
    for message in warnings:
        print(f"[AVISO] {message}")
    for message in errors:
        print(f"[ERRO] {message}")
    print()
    print(f"Resultado: {len(passes)} OK, {len(warnings)} aviso(s), {len(errors)} erro(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
