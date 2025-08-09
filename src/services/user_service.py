from __future__ import annotations
from typing import Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from src.models import User, Transaction, TransactionType


async def get_or_create_user(session: AsyncSession, telegram_id: int, username: Optional[str], first_name: Optional[str], language: Optional[str]) -> User:
    res = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = res.scalars().first()
    if user is None:
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            language=language or "pt",
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
    else:
        changed = False
        if username and user.username != username:
            user.username = username
            changed = True
        if first_name and user.first_name != first_name:
            user.first_name = first_name
            changed = True
        if language and user.language != language:
            user.language = language
            changed = True
        if changed:
            await session.commit()
    return user


async def set_referrer(session: AsyncSession, user: User, referrer_user_id: int) -> None:
    if user.referred_by_user_id or user.id == referrer_user_id:
        return
    res = await session.execute(select(User).where(User.id == referrer_user_id))
    referrer = res.scalars().first()
    if not referrer:
        return
    user.referred_by_user_id = referrer_user_id
    await session.commit()


async def change_balance(session: AsyncSession, user: User, amount_cents: int, *, note: str, related_type: str | None = None, related_id: int | None = None) -> None:
    user.balance_cents += amount_cents
    session.add(Transaction(
        user_id=user.id,
        type=TransactionType.credit if amount_cents >= 0 else TransactionType.debit,
        amount_cents=abs(amount_cents),
        related_type=related_type,
        related_id=related_id,
        note=note,
    ))
    await session.commit()