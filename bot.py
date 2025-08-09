import telebot
from telebot import types

from config import STORE_BOT_TOKEN, ADMIN_IDS
from db import SessionLocal, User, init_db

# Initialize DB tables at startup
init_db()

bot = telebot.TeleBot(STORE_BOT_TOKEN, parse_mode="HTML")

#########################
# Helper: Keyboards
#########################

def main_menu_keyboard() -> types.InlineKeyboardMarkup:
    """Creates the main user menu keyboard."""
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("📜 Logins | Contas Premium", callback_data="menu_services"),
        types.InlineKeyboardButton("👤 Perfil", callback_data="menu_profile"),
        types.InlineKeyboardButton("💰 Recarga", callback_data="menu_topup"),
        types.InlineKeyboardButton("🆘 Suporte", callback_data="menu_support"),
        types.InlineKeyboardButton("🔍 Pesquisar Serviço", callback_data="menu_search"),
    )
    return kb


def admin_menu_keyboard() -> types.InlineKeyboardMarkup:
    """Creates the admin panel keyboard."""
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🛠️ Gerenciar Serviços", callback_data="adm_services"),
        types.InlineKeyboardButton("👥 Configurar Usuários", callback_data="adm_users"),
        types.InlineKeyboardButton("💳 Configurar Pagamentos", callback_data="adm_payments"),
        types.InlineKeyboardButton("📦 Estoque & Logs", callback_data="adm_stock_logs"),
    )
    return kb

#########################
# Command Handlers
#########################


@bot.message_handler(commands=["start"])
def handle_start(message: types.Message):
    """Handle /start command."""
    user_first = message.from_user.first_name or "usuário"
    # Check if user exists; if not, create record and show welcome text
    with SessionLocal() as session:
        user_db = session.query(User).filter_by(telegram_id=message.from_user.id).first()
        if not user_db:
            user_db = User(
                telegram_id=message.from_user.id,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
                username=message.from_user.username,
            )
            session.add(user_db)
            session.commit()
            welcome_text = (
                f"<b>Olá, {user_first}! 👋</b>\n\n"
                "Bem-vindo ao <b>JOAZINHO STORE</b>!\n"
                "Escolha uma opção abaixo para começar:"
            )
            bot.send_message(message.chat.id, welcome_text, reply_markup=main_menu_keyboard())
        else:
            # Already registered user, show main menu directly
            bot.send_message(message.chat.id, "Menu principal:", reply_markup=main_menu_keyboard())


@bot.message_handler(commands=["adm", "admin"])
def handle_admin(message: types.Message):
    """Restricted admin command."""
    if message.from_user.id not in ADMIN_IDS:
        bot.reply_to(message, "❌ Você não tem permissão para acessar o painel administrativo.")
        return
    bot.reply_to(message, "⚙️ <b>Painel Administrativo</b>\nEscolha uma opção:", reply_markup=admin_menu_keyboard())

#########################
# Callback Query Handlers (stubs)
#########################


@bot.callback_query_handler(func=lambda call: call.data.startswith("menu_"))
def process_main_menu(call: types.CallbackQuery):
    if call.data == "menu_services":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "Lista de serviços (em desenvolvimento)...")
    elif call.data == "menu_profile":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "Seu perfil (em desenvolvimento)...")
    elif call.data == "menu_topup":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "Processo de recarga (em desenvolvimento)...")
    elif call.data == "menu_support":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "Suporte: @seuSuporte")
    elif call.data == "menu_search":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "Digite o nome do serviço que deseja buscar:")


@bot.callback_query_handler(func=lambda call: call.data.startswith("adm_"))
def process_admin_menu(call: types.CallbackQuery):
    if call.from_user.id not in ADMIN_IDS:
        bot.answer_callback_query(call.id, "Acesso negado", show_alert=True)
        return
    # Further admin callbacks processing (to be implemented)
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, f"Função '{call.data}' em desenvolvimento...")


if __name__ == "__main__":
    print("Bot iniciado...")
    bot.infinity_polling()
