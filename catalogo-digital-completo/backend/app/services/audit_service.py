from sqlalchemy.orm import Session

from ..models.security_privacy import AuditLog


def write_audit(
    db: Session,
    *,
    action: str,
    store_id: int | None = None,
    user_id: int | None = None,
    entity_type: str | None = None,
    entity_id: str | int | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    metadata: dict | None = None,
) -> AuditLog:
    row = AuditLog(
        action=action,
        store_id=store_id,
        user_id=user_id,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        ip_address=(ip_address or "")[:64] or None,
        user_agent=(user_agent or "")[:300] or None,
        metadata_json=metadata or {},
    )
    db.add(row)
    return row
