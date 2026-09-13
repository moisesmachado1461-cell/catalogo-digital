from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from .config import settings
from .database import engine
from .middleware_security import (
    AuthRateLimitMiddleware,
    RequestIdMiddleware,
    RequestLogMiddleware,
    SecurityHeadersMiddleware,
)
from .observability import configure_observability
from .routes.auth import router as auth_router
from .routes.assistant import router as assistant_router
from .routes.business import router as business_router
from .routes.billing import admin_router as billing_admin_router
from .routes.billing import public_router as billing_public_router
from .routes.billing import super_router as billing_super_router
from .routes.catalog import admin_router as catalog_admin_router
from .routes.catalog import public_router as catalog_public_router
from .routes.customer import router as customer_router
from .routes.marketing import admin_router as marketing_admin_router
from .routes.marketing import public_router as marketing_public_router
from .routes.orders import admin_router as orders_admin_router
from .routes.orders import public_router as orders_public_router
from .routes.payments import admin_router as payments_admin_router
from .routes.payments import public_router as payments_public_router
from .routes.payment_gateways import admin_router as payment_gateways_admin_router
from .routes.payment_gateways import public_router as payment_gateways_public_router
from .routes.privacy import admin_router as privacy_admin_router
from .routes.privacy import public_router as privacy_public_router
from .routes.quotes import admin_router as quotes_admin_router
from .routes.quotes import public_router as quotes_public_router
from .routes.reports import router as reports_admin_router
from .routes.reservations import admin_router as reservations_admin_router
from .routes.reservations import public_router as reservations_public_router
from .routes.services import admin_router as services_admin_router
from .routes.services import appointments_admin_router
from .routes.services import public_router as services_public_router
from .routes.stores import admin_router as stores_admin_router
from .routes.stores import public_router as stores_public_router
from .routes.subscriptions import admin_router as subscriptions_admin_router
from .routes.subscriptions import public_router as plans_public_router
from .routes.subscriptions import super_router as subscriptions_super_router
from .routes.super_admin import router as super_admin_router
from .routes.uploads import router as uploads_admin_router
from .storage import storage_health
from .version import APP_VERSION

settings.validate_for_runtime()
configure_observability()

app = FastAPI(title=settings.app_name, version=APP_VERSION)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLogMiddleware)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(AuthRateLimitMiddleware)

dev_origin_regex = None
if settings.environment.lower() != "production":
    # Permite testar em celular/tablet na mesma rede local, mantendo produção restrita.
    dev_origin_regex = r"^https?://(localhost|127\.0\.0\.1|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})(:\d+)?$"

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_origin_regex=dev_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(assistant_router)
app.include_router(customer_router)
app.include_router(privacy_public_router)
app.include_router(privacy_admin_router)
app.include_router(reports_admin_router)
app.include_router(plans_public_router)
app.include_router(subscriptions_admin_router)
app.include_router(subscriptions_super_router)
app.include_router(billing_public_router)
app.include_router(billing_admin_router)
app.include_router(billing_super_router)
app.include_router(super_admin_router)
app.include_router(uploads_admin_router)
app.include_router(stores_public_router)
app.include_router(stores_admin_router)
app.include_router(business_router)
app.include_router(catalog_public_router)
app.include_router(catalog_admin_router)
app.include_router(orders_public_router)
app.include_router(orders_admin_router)
app.include_router(marketing_public_router)
app.include_router(reservations_public_router)
app.include_router(reservations_admin_router)
app.include_router(payments_public_router)
app.include_router(payments_admin_router)
app.include_router(payment_gateways_public_router)
app.include_router(payment_gateways_admin_router)
app.include_router(marketing_admin_router)
app.include_router(services_public_router)
app.include_router(services_admin_router)
app.include_router(appointments_admin_router)
app.include_router(quotes_public_router)
app.include_router(quotes_admin_router)

# Mantemos a rota /uploads em desenvolvimento e para compatibilidade com arquivos
# antigos. Novos uploads usam storage externo quando STORAGE_PROVIDER=s3 ou cloudinary.
upload_root = Path(settings.upload_dir)
if not upload_root.is_absolute():
    upload_root = (Path.cwd() / upload_root).resolve()
upload_root.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(upload_root)), name="uploads")


@app.get("/api/health")
def health():
    database_ok = False
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        database_ok = True
    except Exception:
        database_ok = False

    storage = storage_health()
    # Banco é obrigatório. Storage local em produção mantém o site de pé, mas
    # health deixa claro que ele ainda não é persistente.
    status_value = "ok" if database_ok else "degraded"
    payload = {
        "status": status_value,
        "environment": settings.environment,
        "version": APP_VERSION,
        "database": "ok" if database_ok else "error",
        "storage": storage,
    }
    return JSONResponse(status_code=200 if database_ok else 503, content=payload)
