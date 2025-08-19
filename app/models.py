from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, Float, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    phone: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120), default="")
    balance: Mapped[float] = mapped_column(Float, default=0.0)
    bonus: Mapped[float] = mapped_column(Float, default=0.0)
    role: Mapped[str] = mapped_column(String(50), default="Cliente")
    referrer: Mapped[str] = mapped_column(String(50), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    purchases: Mapped[list["Purchase"]] = relationship(back_populates="user")
    pix_invoices: Mapped[list["PixInvoice"]] = relationship(back_populates="user")


class FloodState(Base):
    __tablename__ = "flood_states"

    phone: Mapped[str] = mapped_column(String(20), primary_key=True)
    penalty_seconds: Mapped[int] = mapped_column(Integer, default=0)
    last_violation_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150))
    price: Mapped[float] = mapped_column(Float)
    stock: Mapped[int] = mapped_column(Integer, default=0)
    description: Mapped[str] = mapped_column(Text, default="")
    warranty_days: Mapped[int] = mapped_column(Integer, default=30)

    purchases: Mapped[list["Purchase"]] = relationship(back_populates="product")


class Purchase(Base):
    __tablename__ = "purchases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    price_paid: Mapped[float] = mapped_column(Float)
    delivered_text: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped[User] = relationship(back_populates="purchases")
    product: Mapped[Product] = relationship(back_populates="purchases")


class PixInvoice(Base):
    __tablename__ = "pix_invoices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    amount: Mapped[float] = mapped_column(Float)
    code: Mapped[str] = mapped_column(Text)
    qrcode_url: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending|paid|expired
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped[User] = relationship(back_populates="pix_invoices")


class UserState(Base):
    __tablename__ = "user_states"

    phone: Mapped[str] = mapped_column(String(20), primary_key=True)
    context: Mapped[str] = mapped_column(String(50), default="")
    data: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
