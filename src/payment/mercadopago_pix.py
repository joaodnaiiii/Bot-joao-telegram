import base64
from mercadopago import SDK
from src.payment.base import PaymentProvider, CreatedInvoice
from src.config import settings


class MercadoPagoPixProvider(PaymentProvider):
    def __init__(self):
        if not settings.mp_access_token:
            raise RuntimeError("MP_ACCESS_TOKEN not configured")
        self.sdk = SDK(settings.mp_access_token)

    async def create_invoice(self, amount_cents: int, description: str, metadata: dict) -> CreatedInvoice:
        amount = amount_cents / 100.0
        # Mercado Pago requires amounts with 2 decimals
        payment_data = {
            "transaction_amount": round(amount, 2),
            "description": description,
            "payment_method_id": "pix",
            "payer": {"email": "comprador@example.com"},
            "metadata": metadata,
        }
        # SDK is sync; run in thread would be ideal, but ok for short calls
        result = await self._run_sync(self.sdk.payment().create, payment_data)
        data = result["response"]
        external_id = str(data.get("id"))
        pio = data.get("point_of_interaction", {})
        qr_data = pio.get("transaction_data", {})
        qr_text = qr_data.get("qr_code")
        qr_b64 = qr_data.get("qr_code_base64")
        # ensure base64 without prefix
        if qr_b64 and qr_b64.startswith("data:image/png;base64,"):
            qr_b64 = qr_b64.split(",", 1)[1]
        return CreatedInvoice(external_id=external_id, amount_cents=amount_cents, qr_code_text=qr_text, qr_code_base64=qr_b64)

    async def get_status(self, external_id: str) -> str:
        result = await self._run_sync(self.sdk.payment().get, external_id)
        status = result["response"].get("status")
        # map to our statuses
        if status in ("approved",):
            return "paid"
        if status in ("cancelled", "rejected"):
            return "canceled"
        return "pending"

    async def _run_sync(self, func, *args, **kwargs):
        import asyncio
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: func(*args, **kwargs))