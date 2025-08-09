import asyncio
import base64
from src.payment.base import PaymentProvider, CreatedInvoice


class MockPaymentProvider(PaymentProvider):
    def __init__(self):
        self._statuses: dict[str, str] = {}

    async def create_invoice(self, amount_cents: int, description: str, metadata: dict) -> CreatedInvoice:
        external_id = f"mock_{len(self._statuses)+1}"
        self._statuses[external_id] = "pending"
        qr_text = f"MOCKPIX|{external_id}|{amount_cents}"
        qr_b64 = base64.b64encode(qr_text.encode()).decode()
        # simulate async auto payment
        asyncio.create_task(self._auto_pay(external_id))
        return CreatedInvoice(external_id=external_id, amount_cents=amount_cents, qr_code_text=qr_text, qr_code_base64=qr_b64)

    async def _auto_pay(self, external_id: str):
        await asyncio.sleep(5)
        self._statuses[external_id] = "paid"

    async def get_status(self, external_id: str) -> str:
        return self._statuses.get(external_id, "pending")