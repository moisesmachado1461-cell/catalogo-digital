from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from .database import get_db
from .models.user import User
from .models.store import Store
from .security import decode_subject, oauth2_scheme

STORE_ADMIN_ROLE = "ADMINISTRADOR_DA_LOJA"
SUPER_ADMIN_ROLE = "SUPER_ADMINISTRADOR"


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    try:
        user_id = int(decode_subject(token))
    except (TypeError, ValueError):
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
