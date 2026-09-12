from datetime import datetime, timedelta, timezone
import hashlib

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..dependencies import get_current_user
from ..models.user import User
from ..schemas.auth import LoginRequest, TokenResponse
from ..security import create_access_token, verify_password
from ..services.audit_service import write_audit

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _aware(value):
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def _email_fingerprint(email: str) -> str:
    return hashlib.sha256(email.lower().strip().encode("utf-8")).hexdigest()[:16]


def _authenticate_user(db: Session, email: str, password: str, request: Request) -> User:
    normalized = email.lower().strip()
    now = datetime.now(timezone.utc)
    user = db.query(User).filter(User.email == normalized).first()

    if user and user.locked_until and _aware(user.locked_until) > now:
        write_audit(
            db,
            action="LOGIN_BLOCKED",
            store_id=user.store_id,
            user_id=user.id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        db.commit()
        raise HTTPException(status_code=429, detail="Muitas tentativas. Aguarde alguns minutos e tente novamente.")

    valid = bool(user and user.is_active and verify_password(password, user.password_hash))
    if not valid:
        if user:
            user.failed_login_attempts = int(user.failed_login_attempts or 0) + 1
            if user.failed_login_attempts >= settings.max_login_attempts:
                user.locked_until = now + timedelta(minutes=settings.login_lock_minutes)
                user.failed_login_attempts = 0
        write_audit(
            db,
            action="LOGIN_FAILED",
            store_id=user.store_id if user else None,
            user_id=user.id if user else None,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            metadata={"email_fingerprint": _email_fingerprint(normalized)},
        )
        db.commit()
        raise HTTPException(status_code=401, detail="E-mail ou senha inválidos")

    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_at = now
    user.last_login_ip = request.client.host if request.client else None
    write_audit(
        db,
        action="LOGIN_SUCCESS",
        store_id=user.store_id,
        user_id=user.id,
        ip_address=user.last_login_ip,
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = _authenticate_user(db, data.email, data.password, request)
    return TokenResponse(access_token=create_access_token(str(user.id), user.token_version))


@router.post("/token", response_model=TokenResponse)
def oauth2_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = _authenticate_user(db, form_data.username, form_data.password, request)
    return TokenResponse(access_token=create_access_token(str(user.id), user.token_version))


@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role,
        "store_id": current_user.store_id,
        "last_login_at": current_user.last_login_at,
    }
