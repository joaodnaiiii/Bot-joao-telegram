from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import secrets


@dataclass
class PixCharge:
    code: str
    qrcode_url: str
    amount: float
    expires_at: datetime


def generate_mock_pix(amount: float) -> PixCharge:
    token = secrets.token_hex(16)
    code = (
        "00020101021226830014BR.GOV.BCB.PIX2561qrcodespix.sejaefi.com.br/" + token + "53039865802BR5905EFISA6008SAOPAULO62070503***6304E477"
    )
    qrcode_url = f"https://qrcode.example/{token}"
    expires_at = datetime.utcnow() + timedelta(minutes=30)
    return PixCharge(code=code, qrcode_url=qrcode_url, amount=amount, expires_at=expires_at)
