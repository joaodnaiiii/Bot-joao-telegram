from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass
class CreatedInvoice:
    external_id: str
    amount_cents: int
    qr_code_text: Optional[str]
    qr_code_base64: Optional[str]


class PaymentProvider:
    async def create_invoice(self, amount_cents: int, description: str, metadata: dict) -> CreatedInvoice:
        raise NotImplementedError

    async def get_status(self, external_id: str) -> str:
        """Return one of: pending, paid, expired, canceled"""
        raise NotImplementedError