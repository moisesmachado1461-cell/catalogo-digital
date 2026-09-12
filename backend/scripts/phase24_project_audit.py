"""Auditoria local automatizada da Fase 24.1.

Não acessa segredos e não altera banco. Execute a partir de backend:
    python scripts/phase24_project_audit.py
"""
from __future__ import annotations

import ast
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
ROUTES = BACKEND / "app" / "routes"
MIGRATIONS = BACKEND / "alembic" / "versions"

errors: list[str] = []
warnings: list[str] = []
passes: list[str] = []


def ok(message: str) -> None:
    passes.append(message)


def fail(message: str) -> None:
    errors.append(message)


def warn(message: str) -> None:
    warnings.append(message)


def check_python_syntax() -> None:
    files = list((BACKEND / "app").rglob("*.py")) + list((BACKEND / "scripts").rglob("*.py"))
    for path in files:
        try:
            compile(path.read_text(encoding="utf-8"), str(path), "exec")
        except Exception as exc:
            fail(f"Python inválido: {path.relative_to(ROOT)}: {exc}")
    if not any(x.startswith("Python inválido") for x in errors):
        ok(f"Sintaxe Python válida em {len(files)} arquivo(s)")


def check_js_syntax() -> None:
    node = shutil.which("node")
    files = list((FRONTEND / "js").glob("*.js")) + [FRONTEND / "service-worker.js"]
    if not node:
        warn("Node.js não encontrado; a verificação sintática de JavaScript foi ignorada")
        return
    for path in files:
        proc = subprocess.run([node, "--check", str(path)], capture_output=True, text=True)
        if proc.returncode:
            fail(f"JavaScript inválido: {path.relative_to(ROOT)}: {proc.stderr.strip()}")
    if not any(x.startswith("JavaScript inválido") for x in errors):
        ok(f"Sintaxe JavaScript válida em {len(files)} arquivo(s)")


def migration_value(path: Path, name: str) -> str | None:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            if isinstance(node.value, ast.Constant):
                return node.value.value
    return None


def check_migration_chain() -> None:
    revisions: dict[str, str | None] = {}
    for path in sorted(MIGRATIONS.glob("*.py")):
        rev = migration_value(path, "revision")
        down = migration_value(path, "down_revision")
        if not rev:
            fail(f"Migration sem revision: {path.name}")
            continue
        if rev in revisions:
            fail(f"Revision duplicada: {rev}")
        revisions[rev] = down
    referenced = {down for down in revisions.values() if down}
    heads = sorted(set(revisions) - referenced)
    missing = sorted({down for down in revisions.values() if down and down not in revisions})
    if missing:
        fail(f"Migration aponta para revision inexistente: {', '.join(missing)}")
    if len(heads) != 1:
        fail(f"A cadeia Alembic deveria ter 1 head; encontrados: {heads}")
    elif heads:
        ok(f"Cadeia Alembic íntegra; head atual: {heads[0]}")


def check_gitignore() -> None:
    content = (ROOT / ".gitignore").read_text(encoding="utf-8")
    required = [".env", "*.db", "backend/backups/", "backend/uploads/"]
    missing = [item for item in required if item not in content]
    if missing:
        fail(f".gitignore sem proteções esperadas: {', '.join(missing)}")
    else:
        ok(".gitignore protege ambiente, banco local, uploads e backups")


def _versionable_files() -> list[Path]:
    """Return tracked and non-ignored untracked files.

    This keeps local environments (.venv), databases, uploads and other
    gitignored runtime data out of the secret hygiene audit.
    """
    git = shutil.which("git")
    if git:
        proc = subprocess.run(
            [git, "-C", str(ROOT), "ls-files", "--cached", "--others", "--exclude-standard"],
            capture_output=True,
            text=True,
        )
        if proc.returncode == 0:
            return [ROOT / line for line in proc.stdout.splitlines() if line.strip()]

    excluded_parts = {".git", ".venv", "venv", "__pycache__", "backups", "uploads"}
    return [
        path
        for path in ROOT.rglob("*")
        if path.is_file() and not any(part in excluded_parts for part in path.parts)
    ]


def check_secret_hygiene() -> None:
    tracked = _versionable_files()
    risky_patterns = [
        re.compile(r"AKIA[0-9A-Z]{16}"),
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
        re.compile(r"postgres(?:ql)?://[^\s:@/]+:[^\s@/]+@", re.I),
    ]
    found = []
    for path in tracked:
        if path.resolve() == Path(__file__).resolve():
            continue
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".ico", ".zip", ".gz"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue
        if path.name == ".env.example":
            continue
        if any(pattern.search(text) for pattern in risky_patterns):
            found.append(str(path.relative_to(ROOT)))
    if found:
        fail("Possível segredo/URL com credencial em arquivo do projeto: " + ", ".join(found))
    else:
        ok("Nenhum padrão óbvio de segredo privado foi encontrado nos arquivos versionáveis")


def check_cors_and_version() -> None:
    config = (BACKEND / "app" / "config.py").read_text(encoding="utf-8")
    main = (BACKEND / "app" / "main.py").read_text(encoding="utf-8")
    version = (BACKEND / "app" / "version.py").read_text(encoding="utf-8")
    if '"*" in self.allowed_origins' not in config:
        fail("Proteção contra CORS '*' em produção não encontrada")
    else:
        ok("CORS wildcard é bloqueado em produção")
    if "APP_VERSION" not in main or 'APP_VERSION = "24.4.1"' not in version:
        fail("Versão centralizada 24.4.1 não encontrada")
    else:
        ok("Versão do backend centralizada em APP_VERSION=24.4.1")


def check_route_guards() -> None:
    # Heurística conservadora: cada módulo que declara rota /api/admin deve usar
    # a dependência tenant-aware; cada módulo de /api/super-admin deve exigir Super Admin.
    admin_issues = []
    super_issues = []
    for path in ROUTES.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        if 'prefix="/api/admin' in text:
            if "get_current_store_id" not in text and "get_current_store_admin" not in text:
                admin_issues.append(path.name)
        if 'prefix="/api/super-admin' in text:
            if "get_current_super_admin" not in text:
                super_issues.append(path.name)
    if admin_issues:
        fail("Módulos Admin sem guarda tenant detectável: " + ", ".join(admin_issues))
    else:
        ok("Todos os módulos /api/admin possuem guarda tenant detectável")
    if super_issues:
        fail("Módulos Super Admin sem guarda de papel detectável: " + ", ".join(super_issues))
    else:
        ok("Todos os módulos /api/super-admin possuem guarda de Super Admin detectável")


def check_frontend_links() -> None:
    missing = []
    attr_re = re.compile(r'(?:src|href)=["\']([^"\']+)["\']', re.I)
    for page in FRONTEND.glob("*.html"):
        text = page.read_text(encoding="utf-8")
        for value in attr_re.findall(text):
            if value.startswith(("http://", "https://", "mailto:", "tel:", "#", "data:")):
                continue
            clean = value.split("?", 1)[0].split("#", 1)[0]
            if not clean:
                continue
            target = (page.parent / clean).resolve()
            try:
                target.relative_to(FRONTEND.resolve())
            except ValueError:
                continue
            if not target.exists():
                missing.append(f"{page.name} -> {value}")
    if missing:
        fail("Referências locais quebradas: " + "; ".join(sorted(set(missing))))
    else:
        ok("HTMLs não possuem referências locais quebradas detectáveis")



def check_backup_recovery() -> None:
    required = [
        ROOT / ".github" / "workflows" / "database-backup.yml",
        ROOT / ".github" / "workflows" / "restore-drill.yml",
        BACKEND / "scripts" / "backup_common.py",
        BACKEND / "scripts" / "backup_database.py",
        BACKEND / "scripts" / "verify_backup.py",
        BACKEND / "scripts" / "restore_database.py",
        BACKEND / "scripts" / "disaster_recovery_drill.py",
        BACKEND / ".env.example",
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
    if missing:
        fail("Arquivos de backup/recuperação ausentes: " + ", ".join(missing))
    else:
        ok("Backup criptografado, restore drill e workflows de recuperação estão presentes")


def main() -> int:
    checks = [
        check_python_syntax,
        check_js_syntax,
        check_migration_chain,
        check_gitignore,
        check_secret_hygiene,
        check_cors_and_version,
        check_route_guards,
        check_frontend_links,
        check_backup_recovery,
    ]
    for check in checks:
        check()

    print("CATÁLOGO DIGITAL — AUDITORIA FASE 24.4.1")
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
