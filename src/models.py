from __future__ import annotations
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    Enum,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from src.db import Base
import enum


class OrderStatus(str, enum.Enum):
    pending = "pending"
    paid = "paid"
    delivered = "delivered"
    failed = "failed"


class InvoiceStatus(str, enum.Enum):
    pending = "pending"
    paid = "paid"
    expired = "expired"
    canceled = "canceled"


class InvoiceType(str, enum.Enum):
    order = "order"
    topup = "topup"


class TransactionType(str, enum.Enum):
    credit = "credit"
    debit = "debit"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True, index=True, nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String(255))
    first_name: Mapped[Optional[str]] = mapped_column(String(255))
    language: Mapped[str] = mapped_column(String(5), default="pt")
    balance_cents: Mapped[int] = mapped_column(Integer, default=0)
    referred_by_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    affiliate_commission_cents_total: Mapped[int] = mapped_column(Integer, default=0)

    referred_by: Mapped[Optional["User"]] = relationship("User", remote_side=[id])


class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    category: Mapped[Optional[str]] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    price_cents: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    items: Mapped[list["ServiceItem"]] = relationship("ServiceItem", back_populates="service")


class ServiceItem(Base):
    __tablename__ = "service_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"), index=True)
    credential_encrypted: Mapped[str] = mapped_column(Text)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    service: Mapped[Service] = relationship("Service", back_populates="items")


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    amount_cents: Mapped[int] = mapped_column(Integer)
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), default=OrderStatus.pending)
    delivery_payload: Mapped[Optional[str]] = mapped_column(Text)

    user: Mapped[User] = relationship("User")
    service: Mapped[Service] = relationship("Service")


class TopUp(Base):
    __tablename__ = "topups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    amount_cents: Mapped[int] = mapped_column(Integer)
    status: Mapped[InvoiceStatus] = mapped_column(Enum(InvoiceStatus), default=InvoiceStatus.pending)

    user: Mapped[User] = relationship("User")


class PaymentInvoice(Base):
    __tablename__ = "payment_invoices"
    __table_args__ = (
        UniqueConstraint("provider", "external_id", name="uq_provider_external"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    provider: Mapped[str] = mapped_column(String(50))
    external_id: Mapped[str] = mapped_column(String(255))
    type: Mapped[InvoiceType] = mapped_column(Enum(InvoiceType))
    ref_id: Mapped[int] = mapped_column(Integer, index=True)
    amount_cents: Mapped[int] = mapped_column(Integer)
    status: Mapped[InvoiceStatus] = mapped_column(Enum(InvoiceStatus), default=InvoiceStatus.pending)
    qr_code_text: Mapped[Optional[str]] = mapped_column(Text)
    qr_code_base64: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    type: Mapped[TransactionType] = mapped_column(Enum(TransactionType))
    amount_cents: Mapped[int] = mapped_column(Integer)
    related_type: Mapped[Optional[str]] = mapped_column(String(50))
    related_id: Mapped[Optional[int]] = mapped_column(Integer)
    note: Mapped[Optional[str]] = mapped_column(Text)


class AppSetting(Base):
    __tablename__ = "app_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(100), unique=True)
    value: Mapped[str] = mapped_column(Text)


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    actor_user_id: Mapped[Optional[int]] = mapped_column(Integer)
    action: Mapped[str] = mapped_column(String(100))
    details: Mapped[Optional[str]] = mapped_column(Text)