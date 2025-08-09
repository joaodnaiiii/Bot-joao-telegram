from __future__ import annotations
from datetime import datetime
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from src.models import PaymentInvoice, InvoiceStatus, InvoiceType
from src.payment.base import PaymentProvider
from src.payment.mock import MockPaymentProvider
from src.payment.mercadopago_pix import MercadoPagoPixProvider
from src.config import settings


def get_payment_provider() -> PaymentProvider:
    if settings.payment_provider == "mercadopago":
        return MercadoPagoPixProvider()
    return MockPaymentProvider()


async def create_invoice(
    session: AsyncSession,
    *,
    type_: InvoiceType,
    ref_id: int,
    amount_cents: int,
    description: str,
    metadata: dict,
) -> PaymentInvoice:
    provider = get_payment_provider()
    created = await provider.create_invoice(amount_cents, description, metadata)

    invoice = PaymentInvoice(
        provider=settings.payment_provider,
        external_id=created.external_id,
        type=type_,
        ref_id=ref_id,
        amount_cents=amount_cents,
        status=InvoiceStatus.pending,
        qr_code_text=created.qr_code_text,
        qr_code_base64=created.qr_code_base64,
    )
    session.add(invoice)
    await session.commit()
    await session.refresh(invoice)
    return invoice


async def refresh_invoice_status(session: AsyncSession, invoice: PaymentInvoice) -> PaymentInvoice:
    provider = get_payment_provider()
    status_str = await provider.get_status(invoice.external_id)
    new_status = InvoiceStatus(status_str)
    if new_status != invoice.status:
        invoice.status = new_status
        invoice.updated_at = datetime.utcnow()
        await session.commit()
        await session.refresh(invoice)
    return invoice