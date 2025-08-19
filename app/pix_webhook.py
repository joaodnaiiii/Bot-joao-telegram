from __future__ import annotations

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .db import SessionLocal
from .models import PixInvoice, User


router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class PixUpdate(BaseModel):
    invoice_id: int
    status: str  # paid|expired


@router.post("/webhook")
def pix_webhook(payload: PixUpdate, db: Session = Depends(get_db)):
    invoice = db.get(PixInvoice, payload.invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if invoice.status != "pending":
        return {"status": "ignored"}

    if payload.status not in {"paid", "expired"}:
        raise HTTPException(status_code=400, detail="Invalid status")

    invoice.status = payload.status
    if payload.status == "paid":
        user = db.get(User, invoice.user_id)
        user.balance += invoice.amount
    db.commit()
    return {"status": "ok"}
