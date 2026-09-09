from __future__ import annotations

import csv
import io
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..dependencies import get_current_store_id
from ..models.payments import Payment
from ..models.quotes import QuoteRequest
from ..models.reservations import RentalReservation, Reservation
from ..models.sales import Customer, Order
from ..models.services import Appointment
from ..services.report_service import report_overview, report_timeseries, report_top_items
from ..services.subscription_service import require_feature

router = APIRouter(prefix="/api/admin/reports", tags=["reports-admin"])


def _require_reports(db: Session, store_id: int):
    require_feature(db, store_id, "reports")


def _days(period: int) -> int:
    if period not in {7, 30, 90, 365}:
        raise HTTPException(status_code=400, detail="Período inválido. Use 7, 30, 90 ou 365 dias.")
    return period


@router.get("/overview")
def overview(
    period: int = Query(default=30),
    store_id: int = Depends(get_current_store_id),
    db: Session = Depends(get_db),
):
    _require_reports(db, store_id)
    return report_overview(db, store_id, _days(period))


@router.get("/timeseries")
def timeseries(
    period: int = Query(default=30),
    store_id: int = Depends(get_current_store_id),
    db: Session = Depends(get_db),
):
    _require_reports(db, store_id)
    return report_timeseries(db, store_id, _days(period))


@router.get("/top-items")
def top_items(
    period: int = Query(default=30),
    limit: int = Query(default=10, ge=1, le=50),
    store_id: int = Depends(get_current_store_id),
    db: Session = Depends(get_db),
):
    _require_reports(db, store_id)
    return report_top_items(db, store_id, _days(period), limit)


def _csv_response(filename: str, header: list[str], rows: list[list]):
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, delimiter=";", quoting=csv.QUOTE_MINIMAL)
    writer.writerow(header)
    writer.writerows(rows)
    payload = "\ufeff" + buffer.getvalue()
    response = StreamingResponse(iter([payload.encode("utf-8")]), media_type="text/csv; charset=utf-8")
    response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@router.get("/export.csv")
def export_csv(
    report_type: str = Query(alias="type"),
    period: int = Query(default=30),
    store_id: int = Depends(get_current_store_id),
    db: Session = Depends(get_db),
):
    _require_reports(db, store_id)
    days = _days(period)
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    today = datetime.now(timezone.utc).date().isoformat()

    if report_type == "orders":
        rows = db.query(Order).filter(Order.store_id == store_id, Order.created_at >= cutoff).order_by(Order.created_at.desc()).all()
        return _csv_response(
            f"pedidos-{today}.csv",
            ["ID", "Número", "Status", "Pagamento", "Entrega", "Subtotal", "Desconto", "Total", "Criado em"],
            [[r.id, r.order_number, r.status, r.payment_method, r.fulfillment_method, r.subtotal, r.discount_amount, r.total, r.created_at.isoformat()] for r in rows],
        )
    if report_type == "customers":
        rows = db.query(Customer).filter(Customer.store_id == store_id, Customer.created_at >= cutoff).order_by(Customer.created_at.desc()).all()
        return _csv_response(
            f"clientes-{today}.csv",
            ["ID", "Nome", "E-mail", "Telefone", "Cidade", "UF", "Criado em"],
            [[r.id, r.name, r.email or "", r.phone or "", r.city or "", r.state or "", r.created_at.isoformat()] for r in rows],
        )
    if report_type == "appointments":
        rows = db.query(Appointment).options(selectinload(Appointment.service), selectinload(Appointment.professional), selectinload(Appointment.customer)).filter(Appointment.store_id == store_id, Appointment.created_at >= cutoff).order_by(Appointment.starts_at.desc()).all()
        return _csv_response(
            f"agendamentos-{today}.csv",
            ["ID", "Cliente", "Serviço", "Profissional", "Início", "Fim", "Status"],
            [[r.id, r.customer.name if r.customer else "", r.service.name if r.service else "", r.professional.name if r.professional else "", r.starts_at.isoformat(), r.ends_at.isoformat(), r.status] for r in rows],
        )
    if report_type == "payments":
        rows = db.query(Payment).filter(Payment.store_id == store_id, Payment.created_at >= cutoff).order_by(Payment.created_at.desc()).all()
        return _csv_response(
            f"pagamentos-{today}.csv",
            ["ID", "Referência", "ID referência", "Método", "Status", "Valor", "Moeda", "Pago em", "Criado em"],
            [[r.id, r.reference_type, r.reference_id, r.method, r.status, r.amount, r.currency, r.paid_at.isoformat() if r.paid_at else "", r.created_at.isoformat()] for r in rows],
        )
    if report_type == "quotes":
        rows = db.query(QuoteRequest).filter(QuoteRequest.store_id == store_id, QuoteRequest.created_at >= cutoff).order_by(QuoteRequest.created_at.desc()).all()
        return _csv_response(
            f"orcamentos-{today}.csv",
            ["ID", "Título", "Status", "Valor estimado", "Contato", "Criado em"],
            [[r.id, r.title, r.status, r.estimated_amount or "", r.preferred_contact, r.created_at.isoformat()] for r in rows],
        )
    if report_type == "reservations":
        rows = db.query(Reservation).options(selectinload(Reservation.resource), selectinload(Reservation.customer)).filter(Reservation.store_id == store_id, Reservation.created_at >= cutoff).order_by(Reservation.created_at.desc()).all()
        return _csv_response(
            f"reservas-{today}.csv",
            ["ID", "Cliente", "Recurso", "Início", "Fim", "Pessoas", "Status", "Total"],
            [[r.id, r.customer.name if r.customer else "", r.resource.name if r.resource else "", r.starts_at.isoformat(), r.ends_at.isoformat(), r.guests, r.status, r.total] for r in rows],
        )
    if report_type == "rentals":
        rows = db.query(RentalReservation).options(selectinload(RentalReservation.item), selectinload(RentalReservation.customer)).filter(RentalReservation.store_id == store_id, RentalReservation.created_at >= cutoff).order_by(RentalReservation.created_at.desc()).all()
        return _csv_response(
            f"locacoes-{today}.csv",
            ["ID", "Cliente", "Item", "Início", "Fim", "Quantidade", "Dias", "Status", "Total"],
            [[r.id, r.customer.name if r.customer else "", r.item.name if r.item else "", r.starts_at.isoformat(), r.ends_at.isoformat(), r.quantity, r.rental_days, r.status, r.total] for r in rows],
        )

    raise HTTPException(status_code=400, detail="Tipo de relatório inválido")
