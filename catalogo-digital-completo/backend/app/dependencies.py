from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from .database import get_db
from .models.user import User
from .models.sales import CustomerAccount
from .models.store import Store
from .security import decode_token, oauth2_scheme

STORE_ADMIN_ROLE = "ADMINISTRADOR_DA_LOJA"
SUPER_ADMIN_ROLE = "SUPER_ADMINISTRADOR"


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = decode_token(token)
        user_id = int(payload["sub"])
        token_version = int(payload.get("ver", 0) or 0)
    except (TypeError, ValueError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
        )

    user = (
        db.query(User)
        .filter(User.id == user_id, User.is_active.is_(True))
        .first()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado",
        )
    if token_version != int(user.token_version or 0):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Esta sessão foi encerrada. Entre novamente.",
        )
    return user


def get_current_store_admin(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    if current_user.role != STORE_ADMIN_ROLE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso permitido apenas ao administrador da loja",
        )
    if current_user.store_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário administrador não está vinculado a uma loja",
        )
    store_is_active = db.query(Store.id).filter(
        Store.id == current_user.store_id,
        Store.is_active.is_(True),
    ).first()
    if not store_is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta loja está inativa",
        )
    return current_user


def get_current_store_id(
    current_user: User = Depends(get_current_store_admin),
) -> int:
    # Regra multi-tenant central: o store_id vem do usuário autenticado.
    # O frontend não escolhe qual loja será administrada.
    return current_user.store_id


def get_current_super_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != SUPER_ADMIN_ROLE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso permitido apenas ao super administrador",
        )
    return current_user


def _customer_account_from_token(token: str, db: Session) -> CustomerAccount:
    try:
        payload = decode_token(token)
        subject = str(payload["sub"])
        if not subject.startswith("customer:"):
            raise ValueError
        account_id = int(subject.split(":", 1)[1])
        token_version = int(payload.get("ver", 0) or 0)
    except (TypeError, ValueError, KeyError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sessão de cliente inválida")

    account = (
        db.query(CustomerAccount)
        .filter(CustomerAccount.id == account_id, CustomerAccount.is_active.is_(True))
        .first()
    )
    if not account or token_version != int(account.token_version or 0):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sessão de cliente expirada")
    return account


def get_current_customer_account(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> CustomerAccount:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Entre na sua conta para continuar")
    return _customer_account_from_token(authorization.split(" ", 1)[1].strip(), db)


def get_optional_customer_account(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> CustomerAccount | None:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = decode_token(token)
        if not str(payload.get("sub", "")).startswith("customer:"):
            return None
    except HTTPException:
        return None
    return _customer_account_from_token(token, db)
