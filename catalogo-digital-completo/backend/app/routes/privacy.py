from datetime import datetime, timezone
import secrets

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_store_admin, get_current_store_id
from ..models.security_privacy import PrivacyRequest
from ..models.store import Store
from ..models.user import User
from ..schemas.privacy import PrivacyRequestCreate, PrivacyRequestUpdate
from ..services.audit_service import write_audit

public_router = APIRouter(prefix="/api/public", tags=["privacy-public"])
admin_router = APIRouter(prefix="/api/admin/privacy", tags=["privacy-admin"])


@public_router.post("/stores/{slug}/privacy-requests", status_code=201)
def create_privacy_request(slug: str, data: PrivacyRequestCreate, request: Request, db: Session = Depends(get_db)):
    store = db.query(Store).filter(Store.slug == slug, Store.is_active.is_(True)).first()
    if not store:
        raise HTTPException(status_code=404, detail="Loja não encontrada")
    now = datetime.now(timezone.utc)
    row = PrivacyRequest(
        store_id=store.id,
        protocol="LGPD-" + secrets.token_hex(8).upper(),
        request_type=data.request_type,
        status="PENDENTE",
        customer_name=(data.customer_name or "").strip() or None,
        customer_email=str(data.customer_email).lower() if data.customer_email else None,
        customer_phone=(data.customer_phone or "").strip() or None,
        details=(data.details or "").strip() or None,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.flush()
    write_audit(
        db,
        action="PRIVACY_REQUEST_CREATED",
        store_id=store.id,
        entity_type="privacy_request",
        entity_id=row.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        metadata={"request_type": data.request_type},
    )
    db.commit()
    return {"protocol": row.protocol, "status": row.status, "message": "Solicitação registrada para análise."}


@admin_router.get("/requests")
def list_privacy_requests(store_id: int = Depends(get_current_store_id), db: Session = Depends(get_db)):
    rows = db.query(PrivacyRequest).filter(PrivacyRequest.store_id == store_id).order_by(PrivacyRequest.created_at.desc()).all()
    return [
        {
            "id": row.id,
            "protocol": row.protocol,
            "request_type": row.request_type,
            "status": row.status,
            "customer_name": row.customer_name,
            "customer_email": row.customer_email,
            "customer_phone": row.customer_phone,
            "details": row.details,
            "admin_notes": row.admin_notes,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
            "completed_at": row.completed_at,
        }
        for row in rows
    ]


@admin_router.patch("/requests/{request_id}")
def update_privacy_request(
    request_id: int,
    data: PrivacyRequestUpdate,
    request: Request,
    admin: User = Depends(get_current_store_admin),
    db: Session = Depends(get_db),
):
    row = db.query(PrivacyRequest).filter(
        PrivacyRequest.id == request_id,
        PrivacyRequest.store_id == admin.store_id,
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada")
    row.status = data.status
    row.admin_notes = (data.admin_notes or "").strip() or None
    row.updated_at = datetime.now(timezone.utc)
    row.completed_at = row.updated_at if data.status in {"CONCLUIDA", "RECUSADA"} else None
    write_audit(
        db,
        action="PRIVACY_REQUEST_UPDATED",
        store_id=admin.store_id,
        user_id=admin.id,
        entity_type="privacy_request",
        entity_id=row.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        metadata={"status": data.status},
    )
    db.commit()
    return {"id": row.id, "protocol": row.protocol, "status": row.status}


@admin_router.get("/audit-logs")
def list_audit_logs(
    limit: int = 100,
    store_id: int = Depends(get_current_store_id),
    db: Session = Depends(get_db),
):
    from ..models.security_privacy import AuditLog
    safe_limit = min(max(limit, 1), 300)
    rows = db.query(AuditLog).filter(AuditLog.store_id == store_id).order_by(AuditLog.created_at.desc()).limit(safe_limit).all()
    return [
        {
            "id": row.id,
            "action": row.action,
            "user_id": row.user_id,
            "entity_type": row.entity_type,
            "entity_id": row.entity_id,
            "created_at": row.created_at,
            "metadata": row.metadata_json,
        }
        for row in rows
    ]
