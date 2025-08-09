from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import config

Base = declarative_base()
engine = create_engine(config.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    balance = Column(Float, default=0.0)
    is_admin = Column(Boolean, default=False)
    language = Column(String(5), default='pt')
    created_at = Column(DateTime, default=datetime.utcnow)
    referrer_id = Column(Integer, ForeignKey('users.id'))
    
    # Relationships
    purchases = relationship("Purchase", back_populates="user")
    recharges = relationship("Recharge", back_populates="user")
    referrals = relationship("User", backref="referrer", remote_side=[id])

class Service(Base):
    __tablename__ = 'services'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    category = Column(String(100))
    stock = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    accounts = relationship("Account", back_populates="service")
    purchases = relationship("Purchase", back_populates="service")

class Account(Base):
    __tablename__ = 'accounts'
    
    id = Column(Integer, primary_key=True)
    service_id = Column(Integer, ForeignKey('services.id'))
    login = Column(String(200), nullable=False)
    password = Column(String(200), nullable=False)
    additional_info = Column(Text)
    is_sold = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    service = relationship("Service", back_populates="accounts")

class Purchase(Base):
    __tablename__ = 'purchases'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    service_id = Column(Integer, ForeignKey('services.id'))
    account_id = Column(Integer, ForeignKey('accounts.id'))
    amount = Column(Float, nullable=False)
    payment_method = Column(String(50), default='balance')
    status = Column(String(20), default='completed')
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="purchases")
    service = relationship("Service", back_populates="purchases")
    account = relationship("Account")

class Recharge(Base):
    __tablename__ = 'recharges'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    amount = Column(Float, nullable=False)
    pix_key = Column(String(200))
    qr_code = Column(Text)
    status = Column(String(20), default='pending')  # pending, completed, expired
    payment_id = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="recharges")

class Log(Base):
    __tablename__ = 'logs'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    action = Column(String(100), nullable=False)
    details = Column(Text)
    ip_address = Column(String(45))
    created_at = Column(DateTime, default=datetime.utcnow)

def create_tables():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

if __name__ == "__main__":
    create_tables()
    print("Database tables created successfully!")