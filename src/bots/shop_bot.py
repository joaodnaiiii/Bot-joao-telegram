import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, InputMediaPhoto
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.config import settings
from src.db import AsyncSessionLocal, Base, engine
from src.models import User, Service, Order, TopUp, PaymentInvoice, InvoiceStatus, InvoiceType
from src.services.user_service import get_or_create_user, set_referrer
from src.services.inventory_service import list_active_services, get_service
from src.services.order_service import start_order
from src.services.payment_service import refresh_invoice_status
from src.utils.qr import generate_qr_png_bytes
from src.i18n import t


bot = Bot(token=settings.shop_bot_token)
router = Dispatcher()


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def main_menu(lang: str) -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text=t(lang, "menu_services"))
    kb.button(text=t(lang, "menu_profile"))
    kb.button(text=t(lang, "menu_topup"))
    kb.button(text=t(lang, "menu_search"))
    kb.button(text=t(lang, "menu_support"))
    kb.button(text=t(lang, "menu_language"))
    kb.adjust(2, 2, 2)
    return kb.as_markup(resize_keyboard=True)


@router.message(CommandStart())
async def cmd_start(message: Message):
    lang = settings.default_language
    payload = message.text.split(maxsplit=1)
    session: AsyncSession
    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(
            session,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            language=lang,
        )
        # referral: /start ref_<id>
        if len(payload) > 1 and payload[1].startswith("ref_"):
            try:
                ref_id = int(payload[1].split("_", 1)[1])
                await set_referrer(session, user, ref_id)
            except Exception:
                pass
    await message.answer(t(lang, "welcome"), reply_markup=main_menu(lang))


@router.message(F.text.func(lambda x: x is not None and ("Logins" in x or "Premium" in x or "🛍️" in x)))
async def show_services(message: Message):
    lang = settings.default_language
    async with AsyncSessionLocal() as session:
        services = await list_active_services(session)
    if not services:
        await message.answer(t(lang, "no_services"))
        return
    kb = InlineKeyboardBuilder()
    for s in services:
        kb.button(text=f"{s.name} - R$ {s.price_cents/100:.2f}", callback_data=f"svc:{s.id}")
    kb.adjust(1)
    await message.answer(t(lang, "select_service"), reply_markup=kb.as_markup())


@router.callback_query(F.data.startswith("svc:"))
async def select_service(cb: CallbackQuery):
    lang = settings.default_language
    service_id = int(cb.data.split(":", 1)[1])
    async with AsyncSessionLocal() as session:
        service = await get_service(session, service_id)
    if not service:
        await cb.answer("Not found", show_alert=True)
        return
    kb = InlineKeyboardBuilder()
    kb.button(text=t(lang, "buy"), callback_data=f"buy:{service.id}")
    kb.button(text=t(lang, "back"), callback_data="back:menu")
    kb.adjust(2)
    desc = service.description or ""
    await cb.message.answer(
        t(lang, "service_details", name=service.name, price=f"{service.price_cents/100:.2f}", desc=desc),
        reply_markup=kb.as_markup(),
    )
    await cb.answer()


@router.callback_query(F.data.startswith("buy:"))
async def buy_service(cb: CallbackQuery):
    lang = settings.default_language
    service_id = int(cb.data.split(":", 1)[1])
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(User).where(User.telegram_id == cb.from_user.id))
        user = res.scalars().first()
        service = await get_service(session, service_id)
        if not service:
            await cb.answer("Not found", show_alert=True)
            return
        order, invoice = await start_order(session, user, service)
    caption = t(lang, "payment_qr") + "\n" + t(lang, "waiting_payment")
    if invoice.qr_code_base64:
        await cb.message.answer_photo(photo=("qr.png", bytes.fromhex(0).join([]) if False else generate_qr_png_bytes(invoice.qr_code_text or "")), caption=caption)
    elif invoice.qr_code_text:
        await cb.message.answer_photo(photo=("qr.png", generate_qr_png_bytes(invoice.qr_code_text)), caption=caption)
    else:
        await cb.message.answer(caption + f"\n\nCódigo: {invoice.qr_code_text}")

    await cb.answer()

    # Poll payment
    for _ in range(30):
        async with AsyncSessionLocal() as session:
            invoice = await session.get(PaymentInvoice, invoice.id)
            invoice = await refresh_invoice_status(session, invoice)
            if invoice.status == InvoiceStatus.paid:
                await cb.message.answer(t(lang, "paid"))
                from src.services.order_service import handle_invoice_paid
                await handle_invoice_paid(session, invoice)
                # fetch order and send delivery if available
                if invoice.type == InvoiceType.order:
                    from sqlalchemy import select
                    res = await session.execute(select(Order).where(Order.id == invoice.ref_id))
                    order = res.scalars().first()
                    if order and order.delivery_payload:
                        await cb.message.answer(t(lang, "delivered") + f"\n\n{order.delivery_payload}")
                return
        await asyncio.sleep(2)
    await cb.message.answer("Pagamento não identificado ainda. Ele será processado automaticamente ao confirmar.")


@router.message(F.text.func(lambda x: x is not None and ("Perfil" in x or "Profile" in x or "👤" in x)))
async def show_profile(message: Message):
    lang = settings.default_language
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select, func
        from src.models import User, Order, TopUp
        res = await session.execute(select(User).where(User.telegram_id == message.from_user.id))
        user = res.scalars().first()
        res = await session.execute(select(func.count()).select_from(Order).where(Order.user_id == user.id))
        orders = res.scalar_one()
        res = await session.execute(select(func.count()).select_from(TopUp).where(TopUp.user_id == user.id))
        topups = res.scalar_one()
    await message.answer(t(lang, "profile", balance=f"{user.balance_cents/100:.2f}", orders=orders, topups=topups), reply_markup=main_menu(lang))


@router.message(F.text.func(lambda x: x is not None and ("Recarga" in x or "Top-up" in x or "💳" in x)))
async def topup_start(message: Message):
    lang = settings.default_language
    await message.answer(t(lang, "topup_how_much"))


@router.message(F.text.regexp(r"^\d+[\.,]?\d{0,2}$"))
async def topup_amount(message: Message):
    lang = settings.default_language
    try:
        amount_str = message.text.replace(",", ".")
        amount_cents = int(round(float(amount_str) * 100))
    except Exception:
        await message.answer(t(lang, "invalid_amount"))
        return
    async with AsyncSessionLocal() as session:
        from src.models import TopUp, User
        res = await session.execute(select(User).where(User.telegram_id == message.from_user.id))
        user = res.scalars().first()
        topup = TopUp(user_id=user.id, amount_cents=amount_cents)
        session.add(topup)
        await session.commit()
        await session.refresh(topup)
        from src.services.payment_service import create_invoice
        invoice = await create_invoice(session, type_=InvoiceType.topup, ref_id=topup.id, amount_cents=amount_cents, description="Recarga de saldo", metadata={"user_id": user.id, "type": "topup", "topup_id": topup.id})
    caption = t(lang, "payment_qr") + "\n" + t(lang, "waiting_payment")
    if invoice.qr_code_text:
        await message.answer_photo(photo=("qr.png", generate_qr_png_bytes(invoice.qr_code_text)), caption=caption)
    else:
        await message.answer(caption)
    # poll
    for _ in range(30):
        async with AsyncSessionLocal() as session:
            invoice = await session.get(PaymentInvoice, invoice.id)
            invoice = await refresh_invoice_status(session, invoice)
            if invoice.status == InvoiceStatus.paid:
                await message.answer(t(lang, "paid"))
                from src.services.order_service import handle_invoice_paid
                await handle_invoice_paid(session, invoice)
                return
        await asyncio.sleep(2)
    await message.answer("Recarga será aplicada automaticamente ao confirmar o pagamento.")


@router.message(F.text.func(lambda x: x is not None and ("Suporte" in x or "Support" in x or "🛟" in x)))
async def support(message: Message):
    lang = settings.default_language
    await message.answer(t(lang, "support_info"), reply_markup=main_menu(lang))


@router.message(F.text.func(lambda x: x is not None and ("Pesquisar" in x or "Search" in x or "🔎" in x)))
async def search_prompt(message: Message):
    lang = settings.default_language
    await message.answer(t(lang, "search_prompt"))


@router.message(F.text)
async def text_search(message: Message):
    text = message.text.strip()
    lang = settings.default_language
    if not text:
        return
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        from src.models import Service
        res = await session.execute(select(Service).where(Service.is_active == True, Service.name.ilike(f"%{text}%")))
        services = list(res.scalars().all())
    if not services:
        await message.answer(t(lang, "no_services"))
        return
    kb = InlineKeyboardBuilder()
    for s in services:
        kb.button(text=f"{s.name} - R$ {s.price_cents/100:.2f}", callback_data=f"svc:{s.id}")
    kb.adjust(1)
    await message.answer(t(lang, "search_results"), reply_markup=kb.as_markup())


async def main():
    await init_db()
    dp = router
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())