from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.config import settings
from src.db import AsyncSessionLocal, Base, engine
from src.models import User, Service
from src.services.inventory_service import create_service, add_stock_lines


bot = Bot(token=settings.admin_bot_token)
router = Dispatcher()


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def is_admin(user_id: int) -> bool:
    return user_id in settings.admin_telegram_ids


@router.message(Command("adm"))
async def cmd_adm(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("Acesso negado.")
        return
    kb = ReplyKeyboardBuilder()
    kb.button(text="🧩 Serviços")
    kb.button(text="📦 Estoque")
    kb.button(text="👥 Usuários")
    kb.button(text="📈 Relatórios")
    kb.button(text="⚙️ Pagamentos")
    kb.adjust(2, 2, 1)
    await message.answer("Painel Administrativo:", reply_markup=kb.as_markup(resize_keyboard=True))


@router.message(F.text == "🧩 Serviços")
async def admin_services(message: Message):
    if not is_admin(message.from_user.id):
        return
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Adicionar Serviço", callback_data="svc:add")
    # list services
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(Service).order_by(Service.name))
        for s in res.scalars().all():
            kb.button(text=f"✏️ {s.name} (R$ {s.price_cents/100:.2f})", callback_data=f"svc:edit:{s.id}")
    kb.adjust(1)
    await message.answer("Gerenciar Serviços:", reply_markup=kb.as_markup())


@router.callback_query(F.data == "svc:add")
async def svc_add(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        await cb.answer()
        return
    await cb.message.answer("Envie no formato: nome | preco_em_centavos | categoria (opcional) | descricao (opcional)")
    await cb.answer()


@router.message(F.text.regexp(r"^.+\|\s*\d+"))
async def svc_add_parse(message: Message):
    if not is_admin(message.from_user.id):
        return
    parts = [p.strip() for p in message.text.split("|")]
    name = parts[0]
    price_cents = int(parts[1])
    category = parts[2] if len(parts) > 2 else ""
    description = parts[3] if len(parts) > 3 else ""
    async with AsyncSessionLocal() as session:
        svc = await create_service(session, name=name, price_cents=price_cents, description=description, category=category)
    await message.answer(f"✅ Serviço criado: {svc.name} (R$ {svc.price_cents/100:.2f})\nEnvie um arquivo .txt com as credenciais (uma por linha) para adicionar ao estoque deste serviço. Responda com: estoque {svc.id}")


@router.message(F.text.func(lambda x: x and x.lower().startswith("estoque "))) 
async def stock_mode(message: Message):
    if not is_admin(message.from_user.id):
        return
    try:
        service_id = int(message.text.split()[1])
    except Exception:
        await message.answer("Uso: estoque <service_id>")
        return
    await message.answer(f"Envie um arquivo .txt com credenciais. Ele será vinculado ao serviço {service_id}.")


@router.message(F.document)
async def upload_stock(message: Message):
    if not is_admin(message.from_user.id):
        return
    file = message.document
    if not file.file_name.endswith(".txt"):
        await message.answer("Envie um .txt com uma credencial por linha.")
        return
    service_id = None
    # try to find last referenced id in recent messages would require storage; ask inline for now
    await message.answer("Informe o ID do serviço para este estoque (responda: id <service_id>)")


@router.message(F.text.func(lambda x: x and x.lower().startswith("id "))) 
async def set_stock_id(message: Message):
    if not is_admin(message.from_user.id):
        return
    try:
        service_id = int(message.text.split()[1])
    except Exception:
        await message.answer("Uso: id <service_id>")
        return
    await message.answer("Baixando arquivo...")
    file = message.reply_to_message.document if message.reply_to_message and message.reply_to_message.document else None
    if not file:
        await message.answer("Por favor, responda à mensagem do arquivo com: id <service_id>.")
        return
    file_obj = await bot.get_file(file.file_id)
    content = await bot.download_file(file_obj.file_path)
    lines = content.read().decode(errors="ignore").splitlines()
    async with AsyncSessionLocal() as session:
        from src.services.inventory_service import get_service
        svc = await get_service(session, service_id)
        if not svc:
            await message.answer("Serviço não encontrado.")
            return
        count = await add_stock_lines(session, svc, lines)
    await message.answer(f"✅ {count} credenciais adicionadas a {svc.name}.")


async def main():
    await init_db()
    dp = router
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())