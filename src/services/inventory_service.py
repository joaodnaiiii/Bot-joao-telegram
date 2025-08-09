from __future__ import annotations
from typing import Optional, Iterable
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from cryptography.fernet import Fernet, InvalidToken
from base64 import urlsafe_b64encode
from src.config import settings
from src.models import Service, ServiceItem


def _get_fernet() -> Fernet:
    secret = settings.encryption_secret
    if not secret or len(secret) < 32:
        # derive a 32-byte key from provided string
        key = urlsafe_b64encode((secret or "default_secret_key_please_change").ljust(32)[:32].encode())
    else:
        key = urlsafe_b64encode(secret[:32].encode())
    return Fernet(key)


def encrypt_text(plaintext: str) -> str:
    f = _get_fernet()
    return f.encrypt(plaintext.encode()).decode()


def decrypt_text(ciphertext: str) -> str:
    f = _get_fernet()
    try:
        return f.decrypt(ciphertext.encode()).decode()
    except InvalidToken:
        return "(erro ao descriptografar)"


async def list_active_services(session: AsyncSession) -> list[Service]:
    res = await session.execute(select(Service).where(Service.is_active == True).order_by(Service.name))
    return list(res.scalars().all())


async def get_service(session: AsyncSession, service_id: int) -> Optional[Service]:
    res = await session.execute(select(Service).where(Service.id == service_id))
    return res.scalars().first()


async def create_service(session: AsyncSession, name: str, price_cents: int, description: str = "", category: str = "") -> Service:
    service = Service(name=name, price_cents=price_cents, description=description, category=category)
    session.add(service)
    await session.commit()
    await session.refresh(service)
    return service


async def add_stock_lines(session: AsyncSession, service: Service, lines: Iterable[str]) -> int:
    count = 0
    for line in lines:
        line = line.strip()
        if not line:
            continue
        session.add(ServiceItem(service_id=service.id, credential_encrypted=encrypt_text(line)))
        count += 1
    await session.commit()
    return count


async def allocate_credential(session: AsyncSession, service: Service) -> Optional[str]:
    # fetch first unused item
    res = await session.execute(
        select(ServiceItem).where(ServiceItem.service_id == service.id, ServiceItem.is_used == False).order_by(ServiceItem.id).limit(1)
    )
    item = res.scalars().first()
    if not item:
        return None
    item.is_used = True
    await session.commit()
    return decrypt_text(item.credential_encrypted)