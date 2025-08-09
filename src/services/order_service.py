from __future__ import annotations
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models import User, Service, Order, TopUp, PaymentInvoice, InvoiceStatus, InvoiceType
from src.services.payment_service import create_invoice, refresh_invoice_status
from src.services.user_service import change_balance
from src.services.inventory_service import allocate_credential
from src.config import settings


async def start_order(session: AsyncSession, user: User, service: Service) -> tuple[Order, PaymentInvoice]:
    order = Order(user_id=user.id, service_id=service.id, amount_cents=service.price_cents)
    session.add(order)
    await session.commit()
    await session.refresh(order)

    invoice = await create_invoice(
        session,
        type_=InvoiceType.order,
        ref_id=order.id,
        amount_cents=service.price_cents,
        description=f"Compra {service.name}",
        metadata={"user_id": user.id, "order_id": order.id, "type": "order"},
    )
    return order, invoice


async def handle_invoice_paid(session: AsyncSession, invoice: PaymentInvoice) -> None:
    if invoice.type == InvoiceType.order:
        await _deliver_order(session, invoice)
    elif invoice.type == InvoiceType.topup:
        await _apply_topup(session, invoice)


async def _deliver_order(session: AsyncSession, invoice: PaymentInvoice) -> None:
    res = await session.execute(select(Order).where(Order.id == invoice.ref_id))
    order = res.scalars().first()
    if not order or order.status in ("paid", "delivered"):
        return
    # allocate credential
    res = await session.execute(select(Service).where(Service.id == order.service_id))
    service = res.scalars().first()
    credential = await allocate_credential(session, service)
    if not credential:
        return
    order.delivery_payload = credential
    order.paid_at = datetime.utcnow()
    order.status = "delivered"
    await session.commit()


async def _apply_topup(session: AsyncSession, invoice: PaymentInvoice) -> None:
    res = await session.execute(select(TopUp).where(TopUp.id == invoice.ref_id))
    topup = res.scalars().first()
    if not topup or topup.status == InvoiceStatus.paid:
        return
    res = await session.execute(select(User).where(User.id == topup.user_id))
    user = res.scalars().first()
    await change_balance(session, user, topup.amount_cents, note="Recarga Pix", related_type="topup", related_id=topup.id)
    topup.status = InvoiceStatus.paid
    topup.paid_at = datetime.utcnow()
    await session.commit()
    # affiliate commission
    if user.referred_by_user_id:
        res = await session.execute(select(User).where(User.id == user.referred_by_user_id))
        referrer = res.scalars().first()
        if referrer:
            commission = int(topup.amount_cents * settings.affiliate_commission_percent / 100)
            await change_balance(session, referrer, commission, note=f"Comissão indicação {user.id}", related_type="commission", related_id=topup.id)