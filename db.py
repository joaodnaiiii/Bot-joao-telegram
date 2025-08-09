from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, create_engine, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime

from config import DB_URL

engine = create_engine(DB_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)
    first_name = Column(String(255))
    last_name = Column(String(255))
    username = Column(String(255))
    balance = Column(Float, default=0.0)
    referred_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    referrals = relationship("User", backref="referrer", remote_side=[id])
    transactions = relationship("Transaction", back_populates="user")


class Service(Base):
    __tablename__ = "services"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=0)
    active = Column(Boolean, default=True)

    transactions = relationship("Transaction", back_populates="service")


class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    service_id = Column(Integer, ForeignKey("services.id"), nullable=True)  # Nullable for top-ups
    type = Column(String(50))  # purchase, topup
    amount = Column(Float, nullable=False)
    paid = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="transactions")
    service = relationship("Service", back_populates="transactions")


class Log(Base):
    __tablename__ = "logs"
    id = Column(Integer, primary_key=True, index=True)
    level = Column(String(20))
    message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)