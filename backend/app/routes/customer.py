from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session, selectinload

from ..config import settings
from ..database import get_db
from ..dependencies import get_current_customer_account
from ..models.sales import Customer, CustomerAccount, Order
from ..models.services import Appointment
from ..repositories.catalog_repository import get_store_by_slug
from ..schemas.customer import CustomerClaimRequest, CustomerLoginRequest, CustomerRegisterRequest
from ..security import create_access_token, hash_password, verify_password_or_dummy
from ..services.payment_service import payment_for_reference
from .orders import _order_dict
from .services import _appointment_dict

router = APIRouter(prefix="/api/customer", tags=["customer-portal"])


def _aware(value):
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def _account_token(account: CustomerAccount) -> str:
    return create_access_token(f"customer:{account.id}", account.token_version)


def _store_payload(store):
    return {
        "id": store.id,
        "name": store.name,
        "slug": store.slug,
        "logo_url": store.logo_url,
        "primary_color": store.primary_color,
        "secondary_color": store.secondary_color,
        "whatsapp": store.whatsapp,
        "phone": store.phone,
    }


def _account_payload(account: CustomerAccount):
    customer = account.customer
    return {
        "id": account.id,
        "email": account.email,
        "name": customer.name,
        "phone": customer.phone,
        "customer_id": customer.id,
        "store": _store_payload(account.store),
        "last_login_at": account.last_login_at.isoformat() if account.last_login_at else None,
    }


def _tracked_customer(db: Session, store_id: int, tracking_type: str | None, token: str | None):
    if not tracking_type or not token:
        return None
    tracking_type = tracking_type.upper()
    if tracking_type == "ORDER":
        row = db.query(Order).filter(Order.store_id == store_id, Order.public_token == token).first()
    elif tracking_type == "APPOINTMENT":
        row = db.query(Appointment).filter(Appointment.store_id == store_id, Appointment.public_token == token).first()
    else:
        return None
    if not row or not row.customer_id:
        raise HTTPException(status_code=400, detail="O link informado não pode ser usado para criar esta conta")
    return db.query(Customer).filter(Customer.id == row.customer_id, Customer.store_id == store_id).first()


def _customer_has_history(db: Session, customer_id: int) -> bool:
    return bool(
        db.query(Order.id).filter(Order.customer_id == customer_id).first()
        or db.query(Appointment.id).filter(Appointment.customer_id == customer_id).first()
    )


@router.post("/register", status_code=201)
def register_customer(data: CustomerRegisterRequest, db: Session = Depends(get_db)):
    store = get_store_by_slug(db, data.store_slug)
    if not store:
        raise HTTPException(status_code=404, detail="Loja não encontrada")

    email = str(data.email).lower().strip()
    existing_account = (
        db.query(CustomerAccount)
        .filter(CustomerAccount.store_id == store.id, CustomerAccount.email == email)
        .first()
    )
    if existing_account:
        raise HTTPException(status_code=409, detail="Já existe uma conta com este e-mail nesta loja. Faça login.")

    claimed = _tracked_customer(db, store.id, data.tracking_type, data.tracking_token)
    if claimed:
        claimed_email = (claimed.email or "").lower().strip()
        if claimed_email and claimed_email != email:
            raise HTTPException(status_code=403, detail="O e-mail informado não corresponde ao pedido/agendamento deste link")
        customer = claimed
    else:
        customer = (
            db.query(Customer)
            .filter(Customer.store_id == store.id, Customer.email == email)
            .order_by(Customer.id.asc())
            .first()
        )
        if customer and _customer_has_history(db, customer.id):
            raise HTTPException(
                status_code=409,
                detail="Já existem pedidos ou agendamentos para este e-mail. Crie a conta pelo link de acompanhamento para proteger seu histórico.",
            )
        if not customer:
            customer = Customer(
                store_id=store.id,
                name=data.name.strip(),
                email=email,
                phone=data.phone.strip() if data.phone else None,
                is_active=True,
            )
            db.add(customer)
            db.flush()

    customer.name = data.name.strip()
    customer.email = email
    if data.phone:
        customer.phone = data.phone.strip()

    account = CustomerAccount(
        store_id=store.id,
        customer_id=customer.id,
        email=email,
        password_hash=hash_password(data.password),
        is_active=True,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    account = (
        db.query(CustomerAccount)
        .options(selectinload(CustomerAccount.customer), selectinload(CustomerAccount.store))
        .filter(CustomerAccount.id == account.id)
        .one()
    )
    return {"access_token": _account_token(account), "token_type": "bearer", "account": _account_payload(account)}


@router.post("/login")
def login_customer(data: CustomerLoginRequest, request: Request, db: Session = Depends(get_db)):
    store = get_store_by_slug(db, data.store_slug)
    if not store:
        raise HTTPException(status_code=404, detail="Loja não encontrada")
    email = str(data.email).lower().strip()
    account = (
        db.query(CustomerAccount)
        .options(selectinload(CustomerAccount.customer), selectinload(CustomerAccount.store))
        .filter(CustomerAccount.store_id == store.id, CustomerAccount.email == email)
        .first()
    )
    now = datetime.now(timezone.utc)
    if account and account.locked_until and _aware(account.locked_until) > now:
        raise HTTPException(status_code=429, detail="Muitas tentativas. Aguarde alguns minutos e tente novamente.")

    valid = bool(account and account.is_active and verify_password_or_dummy(data.password, account.password_hash))
    if not valid:
        if account:
            account.failed_login_attempts = int(account.failed_login_attempts or 0) + 1
            if account.failed_login_attempts >= settings.max_login_attempts:
                account.locked_until = now + timedelta(minutes=settings.login_lock_minutes)
                account.failed_login_attempts = 0
            db.commit()
        else:
            verify_password_or_dummy(data.password, None)
        raise HTTPException(status_code=401, detail="E-mail ou senha inválidos")

    account.failed_login_attempts = 0
    account.locked_until = None
    account.last_login_at = now
    db.commit()
    db.refresh(account)
    return {"access_token": _account_token(account), "token_type": "bearer", "account": _account_payload(account)}


@router.get("/me")
def customer_me(account: CustomerAccount = Depends(get_current_customer_account)):
    return _account_payload(account)


@router.get("/orders")
def customer_orders(
    account: CustomerAccount = Depends(get_current_customer_account),
    db: Session = Depends(get_db),
):
    orders = (
        db.query(Order)
        .options(selectinload(Order.items), selectinload(Order.customer))
        .filter(Order.store_id == account.store_id, Order.customer_id == account.customer_id)
        .order_by(Order.created_at.desc())
        .all()
    )
    return [_order_dict(row, payment_for_reference(db, account.store_id, "ORDER", row.id)) for row in orders]


@router.get("/appointments")
def customer_appointments(
    account: CustomerAccount = Depends(get_current_customer_account),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(Appointment)
        .options(
            selectinload(Appointment.customer),
            selectinload(Appointment.service),
            selectinload(Appointment.professional),
        )
        .filter(Appointment.store_id == account.store_id, Appointment.customer_id == account.customer_id)
        .order_by(Appointment.starts_at.desc())
        .all()
    )
    return [
        _appointment_dict(row, payment_for_reference(db, account.store_id, "APPOINTMENT", row.id))
        for row in rows
    ]


@router.post("/claim")
def claim_history(
    data: CustomerClaimRequest,
    account: CustomerAccount = Depends(get_current_customer_account),
    db: Session = Depends(get_db),
):
    if data.tracking_type == "ORDER":
        row = (
            db.query(Order)
            .options(selectinload(Order.customer))
            .filter(Order.store_id == account.store_id, Order.public_token == data.tracking_token)
            .first()
        )
    else:
        row = (
            db.query(Appointment)
            .options(selectinload(Appointment.customer))
            .filter(Appointment.store_id == account.store_id, Appointment.public_token == data.tracking_token)
            .first()
        )
    if not row:
        raise HTTPException(status_code=404, detail="Pedido ou agendamento não encontrado")
    if row.customer_id == account.customer_id:
        return {"ok": True, "already_linked": True}
    source_email = (row.customer.email if row.customer else "") or ""
    if source_email.lower().strip() != account.email.lower().strip():
        raise HTTPException(status_code=403, detail="Este acompanhamento pertence a outro cliente")
    row.customer_id = account.customer_id
    db.commit()
    return {"ok": True, "already_linked": False}
