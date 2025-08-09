from fastapi import FastAPI, Request, HTTPException
from src.config import settings
from src.db import AsyncSessionLocal
from src.models import PaymentInvoice, InvoiceStatus
from src.services.payment_service import refresh_invoice_status
from src.services.order_service import handle_invoice_paid

app = FastAPI()


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/webhooks/mercadopago")
async def mp_webhook(request: Request):
    # Mercado Pago sends notifications with data.id referring to payment id
    body = await request.json()
    data = body.get("data", {})
    external_id = str(data.get("id")) if data.get("id") else None
    if not external_id:
        return {"ok": True}
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        res = await session.execute(select(PaymentInvoice).where(PaymentInvoice.provider == "mercadopago", PaymentInvoice.external_id == external_id))
        invoice = res.scalars().first()
        if not invoice:
            return {"ok": True}
        invoice = await refresh_invoice_status(session, invoice)
        if invoice.status == InvoiceStatus.paid:
            await handle_invoice_paid(session, invoice)
    return {"ok": True}