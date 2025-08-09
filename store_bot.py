import telebot
from telebot import types
import config
import utils
from database import SessionLocal, User, Service, Account, Purchase, Recharge, Log
from datetime import datetime, timedelta
import json
import base64
import io
from PIL import Image
import requests

bot = telebot.TeleBot(config.STORE_BOT_TOKEN)

# User states for conversation flow
user_states = {}

# Sample products data (will be managed by admin bot)
SAMPLE_PRODUCTS = [
    {"name": "ACESSO: PAINEL IPTV (10 CREDITOS)", "price": 20.00, "stock": 5, "description": "Aviso Importante:\nInformamos que não realizamos reembolsos via Pix, apenas em créditos no bot, correspondendo aos dias restantes até o vencimento.\nAgradecemos pela compreensão e desejamos boas compras!\n\nObs: O prazo de entrega é até 24 horas.\nObs: Olhe atentamente a o texto da compra.", "guarantee": 30},
    {"name": "Netflix Premium", "price": 15.00, "stock": 10, "description": "Conta Netflix Premium com acesso total", "guarantee": 30},
    {"name": "Disney+ Premium", "price": 12.00, "stock": 8, "description": "Conta Disney+ com todos os filmes e séries", "guarantee": 30},
    {"name": "Amazon Prime", "price": 18.00, "stock": 6, "description": "Conta Amazon Prime Video completa", "guarantee": 30}
]

def get_user_data(telegram_id):
    """Get user data from database"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        if not user:
            user = User(
                telegram_id=telegram_id,
                username="",
                first_name="",
                balance=0.0
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        return user
    finally:
        db.close()

def create_main_keyboard():
    """Create main menu inline keyboard with exact layout"""
    keyboard = types.InlineKeyboardMarkup()
    
    # First row - Logins | Contas Premium (full width)
    keyboard.add(types.InlineKeyboardButton("🎮 Logins | Contas Premium", callback_data="services"))
    
    # Second row - Perfil and Recarga (side by side)
    keyboard.row(
        types.InlineKeyboardButton("👤 Perfil", callback_data="profile"),
        types.InlineKeyboardButton("💰 Recarga", callback_data="recharge")
    )
    
    # Third row - Ranking (full width)
    keyboard.add(types.InlineKeyboardButton("🏆 Ranking", callback_data="ranking"))
    
    # Fourth row - Suporte and Informações (side by side)
    keyboard.row(
        types.InlineKeyboardButton("🆘 Suporte", callback_data="support"),
        types.InlineKeyboardButton("🔍 Informações", callback_data="search")
    )
    
    return keyboard

def create_menu_commands():
    """Create menu commands that appear at bottom"""
    commands = [
        types.BotCommand("start", "🏠 Iniciar bot"),
        types.BotCommand("pix", "💳 Gera um pix para adicionar saldo no bot"),
        types.BotCommand("historico", "📊 Suas compras"),
        types.BotCommand("afiliados", "💰 Ganhe saldo indicando o bot"),
        types.BotCommand("id", "🆔 Exibe seu identificador"),
        types.BotCommand("saldo", "💸 Exibe seu saldo no bot"),
        types.BotCommand("ranking", "🏆 Ranking de usuários do bot"),
        types.BotCommand("termos", "📋 Mostra os termos de uso"),
        types.BotCommand("alertas", "🔔 Seja avisado de cada conta abastecida")
    ]
    bot.set_my_commands(commands)

@bot.message_handler(commands=['start'])
def start_command(message):
    user = get_user_data(message.from_user.id)
    
    # Set menu commands
    create_menu_commands()
    
    welcome_text = f"""🥇 Descubra como nosso bot pode transformar sua experiência de compras! Ele facilita a busca por diversos produtos e serviços, garantindo que você encontre o que precisa com o melhor preço e excelente custo-benefício.

Importante: Não realizamos reembolsos em dinheiro. O suporte estará disponível por até 48 horas após a entrega das informações, com reembolso em créditos no bot, se necessário.

👥 Grupo De Clientes: 
{config.CLIENT_GROUP_LINK}

👨🏻‍💻 Link De Suporte: {config.SUPPORT_USERNAME}

ℹ️ Seus Dados:
├🆔 ID: {user.telegram_id}
├💸 Saldo Atual: R${user.balance:.2f}
├🪪 Usuário: {message.from_user.first_name or 'N/A'}"""

    # Send text message first
    bot.send_message(
        message.chat.id,
        welcome_text
    )
    
    # Send image separately
    try:
        bot.send_photo(
            message.chat.id,
            config.STORE_IMAGE_URL
        )
    except:
        pass  # If image fails, continue without it
    
    # Send buttons as separate message
    bot.send_message(
        message.chat.id,
        "Escolha uma opção:",
        reply_markup=create_main_keyboard()
    )

@bot.callback_query_handler(func=lambda call: call.data == "services")
def show_services(call):
    user = get_user_data(call.from_user.id)
    
    text = f"""🎟 Logins Premium | Acesso Exclusivo 

🏦 Carteira
└ 💸 Saldo Atual: R${user.balance:.2f}"""

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    
    # Add products
    for i, product in enumerate(SAMPLE_PRODUCTS):
        keyboard.add(types.InlineKeyboardButton(
            f"{product['name']} - R${product['price']:.2f}",
            callback_data=f"product_{i}"
        ))
    
    # Back button
    keyboard.add(types.InlineKeyboardButton("⬅️ Voltar", callback_data="back_main"))
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=keyboard
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("product_"))
def show_product_details(call):
    product_id = int(call.data.split("_")[1])
    product = SAMPLE_PRODUCTS[product_id]
    user = get_user_data(call.from_user.id)
    
    text = f"""◎ ══════ ❈ ══════ ◎  
⚜️{product['name']} ⚜️

💵| Preço: R${product['price']:.2f}
💼| Saldo Atual: R${user.balance:.2f}
📥| Estoque Disponível: {product['stock']}

🗒 Descrição: {product['description']}

♻️ Garantia: {product['guarantee']} dias
◎ ══════ ❈ ══════ ◎"""

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("🛒 Comprar Agora", callback_data=f"buy_{product_id}"))
    keyboard.add(types.InlineKeyboardButton("⬅️ Voltar", callback_data="services"))
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=keyboard
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def process_purchase(call):
    product_id = int(call.data.split("_")[1])
    product = SAMPLE_PRODUCTS[product_id]
    user = get_user_data(call.from_user.id)
    
    if user.balance < product['price']:
        # Show insufficient balance message (as alert popup)
        bot.answer_callback_query(
            call.id,
            f"Saldo insuficiente! Faltam\nR${product['price'] - user.balance:.2f} faça uma recarga e tente novamente.\nSeu saldo: R$ {user.balance:.2f}",
            show_alert=True
        )
        return
    
    # Process purchase (simplified)
    db = SessionLocal()
    try:
        user.balance -= product['price']
        db.add(user)
        db.commit()
        
        # In real implementation, you would assign an account here
        success_text = f"""✅ **COMPRA REALIZADA COM SUCESSO!**

🎯 Serviço: {product['name']}
💰 Valor: R${product['price']:.2f}

📧 **SEUS DADOS DE ACESSO:**
👤 Login: `exemplo@email.com`
🔑 Senha: `senha123`
ℹ️ Informações adicionais: Conta válida por 30 dias

⚠️ Guarde essas informações com segurança!"""

        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("⬅️ Voltar ao Menu", callback_data="back_main"))
        
        bot.edit_message_text(
            success_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        
    finally:
        db.close()

@bot.callback_query_handler(func=lambda call: call.data == "profile")
def show_profile(call):
    user = get_user_data(call.from_user.id)
    
    # Get user stats
    db = SessionLocal()
    try:
        purchases_count = db.query(Purchase).filter(Purchase.user_id == user.id).count()
        total_spent = db.query(Purchase).filter(Purchase.user_id == user.id).with_entities(
            db.func.sum(Purchase.amount)
        ).scalar() or 0
        gifts_redeemed = 0  # Placeholder
    finally:
        db.close()
    
    text = f"""🙋‍♂️ Meu perfil

🔍 Veja aqui os detalhes da sua conta:
- 👤 Informações:
🆔 ID da Carteira: {user.telegram_id}
💰 Saldo Atual: R${user.balance:.2f}

────────────── 📊 Suas Movimentações:
ー🛒 Compras Realizadas: {purchases_count}
ー💠 Pix Inseridos: R${total_spent:.2f}
ー🎁 Gifts Resgatados: R${gifts_redeemed:.2f}"""

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("📊 Histórico de Compras", callback_data="purchase_history"))
    keyboard.add(types.InlineKeyboardButton("⬅️ Voltar", callback_data="back_main"))
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=keyboard
    )

@bot.callback_query_handler(func=lambda call: call.data == "purchase_history")
def show_purchase_history(call):
    user = get_user_data(call.from_user.id)
    
    db = SessionLocal()
    try:
        purchases = db.query(Purchase).filter(Purchase.user_id == user.id).all()
        
        if not purchases:
            text = "Você não tem compras no bot. Quando comprar alguma conta, as informações dela ficarão exibidas aqui."
        else:
            # In real implementation, generate PDF/Excel here
            text = "📊 **HISTÓRICO DE COMPRAS**\n\n"
            for purchase in purchases:
                text += f"🛒 {purchase.service.name}\n💰 R${purchase.amount:.2f}\n📅 {purchase.created_at.strftime('%d/%m/%Y %H:%M')}\n\n"
    finally:
        db.close()
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("⬅️ Voltar", callback_data="profile"))
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

@bot.callback_query_handler(func=lambda call: call.data == "recharge")
def show_recharge_menu(call):
    user = get_user_data(call.from_user.id)
    
    text = f"""💼| ID da Carteira: {user.telegram_id}
💵| Saldo Disponível: R${user.balance:.2f}

💡 Selecione uma opção para recarregar:"""

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("💳 PushinPay", callback_data="pushinpay"))
    keyboard.add(types.InlineKeyboardButton("⬅️ Voltar", callback_data="back_main"))
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=keyboard
    )

@bot.callback_query_handler(func=lambda call: call.data == "pushinpay")
def request_recharge_amount(call):
    text = f"""ℹ️ Informe o valor que deseja recarregar:

🔻 Recarga mínima: R${config.MIN_RECHARGE:.2f}

⚠️ Por favor, envie o valor que deseja recarregar agora."""

    user_states[call.from_user.id] = "waiting_recharge_amount"
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id
    )
    
    # Force reply for amount input with store name
    bot.send_message(
        call.message.chat.id,
        f"Resposta a {config.STORE_NAME}",
        reply_markup=types.ForceReply(selective=True)
    )

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == "waiting_recharge_amount")
def process_recharge_amount(message):
    try:
        amount = float(message.text.replace(',', '.'))
        if amount < config.MIN_RECHARGE:
            bot.reply_to(message, f"❌ Valor mínimo para recarga é R${config.MIN_RECHARGE:.2f}")
            return
        
        # Generate PIX payment
        user = get_user_data(message.from_user.id)
        transaction_id = utils.generate_referral_code(user.id) + str(int(datetime.now().timestamp()))[-4:]
        
        # Simulate PushinPay PIX generation
        pix_code = "00020101021226810014br.gov.bcb.pix2559qr.woovi.com/qr/v2/cob/04f784f1-e7e8-4b92-a31b-97d5dedd28dc520400005303986540529.005802BR5909PushinPay6009Sao_Paulo622905257d6eb598cf4d46abb05fbedd963040E64"
        
        text = f"""Gerando pagamento...
💰 Comprar Saldo com Pix Automático:

⏱️ Expira em: {config.PIX_EXPIRY_MINUTES} Minutos  
💵 Valor: R$ {amount:.2f}  
✨ ID da Recarga: {transaction_id}

📃 Atenção: Este código é válido para apenas um único pagamento.  
Se você utilizá-lo mais de uma vez, o saldo adicional será perdido sem direito a reembolso.

💎 Pix Copia e Cola:  
{pix_code}

💡 Dica: Clique no código acima para copiar.  

🇧🇷 Após o pagamento, seu saldo será liberado instantaneamente."""

        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("⏳ Aguardando Pagamento", callback_data=f"check_payment_{transaction_id}"))
        
        bot.send_message(
            message.chat.id,
            text,
            reply_markup=keyboard
        )
        
        # Store recharge in database
        db = SessionLocal()
        try:
            recharge = Recharge(
                user_id=user.id,
                amount=amount,
                payment_id=transaction_id,
                qr_code=pix_code,
                status='pending'
            )
            db.add(recharge)
            db.commit()
        finally:
            db.close()
        
        user_states[message.from_user.id] = None
        
    except ValueError:
        bot.reply_to(message, "❌ Por favor, envie um valor numérico válido.")

@bot.callback_query_handler(func=lambda call: call.data == "ranking")
def show_ranking_menu(call):
    # Show services ranking by default with buttons
    show_services_ranking(call)

@bot.callback_query_handler(func=lambda call: call.data == "rank_services")
def show_services_ranking(call):
    text = """🏆 Ranking dos serviços mais vendidos (deste mês)

1°) Premiere (tela) 🥇 - Com 66 pedidos
2°) Globoplay+canais (tela) 🥈 - Com 66 pedidos
3°) Prime video (tela) 🥉 - Com 65 pedidos
4°) Disney+star premium (tela) - Com 40 pedidos
5°) Iptv premium (mensal) - Com 35 pedidos
6°) Max (tela) - Com 28 pedidos
7°) Youtube premium (convite) - Com 25 pedidos
8°) Netflix premium (tela) - Com 23 pedidos
9°) Globoplay+canais+telecine (tela) - Com 20 pedidos
10°) Grupos vips +30 links +18 (acesso) - Com 19 pedidos"""

    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.row(
        types.InlineKeyboardButton("🎯 Serviços ✅", callback_data="rank_services"),
        types.InlineKeyboardButton("💰 Recargas", callback_data="rank_recharges")
    )
    keyboard.row(
        types.InlineKeyboardButton("🛒 Compras", callback_data="rank_purchases"),
        types.InlineKeyboardButton("💳 Saldo", callback_data="rank_balance")
    )
    keyboard.add(types.InlineKeyboardButton("⬅️ Voltar", callback_data="back_main"))
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=keyboard
    )

@bot.callback_query_handler(func=lambda call: call.data == "rank_recharges")
def show_recharges_ranking(call):
    text = """🏆 Ranking dos usuários que mais recarregaram (deste mês)

1°) Karoline 🥇 - Com R$38,00 em recargas
2°) Alice vendas| ADM ALICE 🥈 - Com R$31,50 em recargas
3°) Gabriel 🥉 - Com R$31,00 em recargas
4°) Pivete 7️⃣ - Com R$30,00 em recargas
5°) unstoppable - Com R$27,50 em recargas
6°) Matheus - Com R$26,50 em recargas
7°) Rebeca - Com R$26,50 em recargas
8°) M - Com R$25,00 em recargas
9°) Rick - Com R$25,00 em recargas
10°) King Vendas - Com R$22,00 em recargas"""

    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.row(
        types.InlineKeyboardButton("🎯 Serviços", callback_data="rank_services"),
        types.InlineKeyboardButton("💰 Recargas ✅", callback_data="rank_recharges")
    )
    keyboard.row(
        types.InlineKeyboardButton("🛒 Compras", callback_data="rank_purchases"),
        types.InlineKeyboardButton("💳 Saldo", callback_data="rank_balance")
    )
    keyboard.add(types.InlineKeyboardButton("⬅️ Voltar", callback_data="back_main"))
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=keyboard
    )

@bot.callback_query_handler(func=lambda call: call.data == "rank_purchases")
def show_purchases_ranking(call):
    text = """🏆 Ranking dos usuários que mais compraram (deste mês)

1°) Pivete 7️⃣ 🥇 - Com 7 compras
2°) Alice vendas| ADM ALICE 🥈 - Com 7 compras
3°) Elaysa 🥉 - Com 7 compras
4°) Clara - Com 7 compras
5°) M - Com 6 compras
6°) Kings Digital _•™ - Com 6 compras
7°) Eduardo - Com 5 compras
8°) Karoline - Com 5 compras
9°) unstoppable - Com 5 compras
10°) lena - Com 4 compras"""

    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.row(
        types.InlineKeyboardButton("🎯 Serviços", callback_data="rank_services"),
        types.InlineKeyboardButton("💰 Recargas", callback_data="rank_recharges")
    )
    keyboard.row(
        types.InlineKeyboardButton("🛒 Compras ✅", callback_data="rank_purchases"),
        types.InlineKeyboardButton("💳 Saldo", callback_data="rank_balance")
    )
    keyboard.add(types.InlineKeyboardButton("⬅️ Voltar", callback_data="back_main"))
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=keyboard
    )

@bot.callback_query_handler(func=lambda call: call.data == "rank_balance")
def show_balance_ranking(call):
    text = """🏆 Ranking dos usuários com mais saldo no bot

1°) Ianh 🥇 - Com R$284,49 de saldo
2°) CH7 METODOS 🥈 - Com R$205,00 de saldo
3°) Mauro (L' 🥉 - Com R$202,70 de saldo
4°) Lucas - Com R$142,06 de saldo
5°) Zoroiptv - Com R$78,00 de saldo
6°) Renan - Com R$69,16 de saldo
7°) pablo - Com R$68,00 de saldo
8°) BRUNÃO - Com R$67,00 de saldo
9°) Henrique - Com R$63,50 de saldo
10°) Marcele - Com R$63,00 de saldo"""

    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.row(
        types.InlineKeyboardButton("🎯 Serviços", callback_data="rank_services"),
        types.InlineKeyboardButton("💰 Recargas", callback_data="rank_recharges")
    )
    keyboard.row(
        types.InlineKeyboardButton("🛒 Compras", callback_data="rank_purchases"),
        types.InlineKeyboardButton("💳 Saldo ✅", callback_data="rank_balance")
    )
    keyboard.add(types.InlineKeyboardButton("⬅️ Voltar", callback_data="back_main"))
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=keyboard
    )

@bot.callback_query_handler(func=lambda call: call.data == "support")
def show_support(call):
    # Redirect to support username
    bot.answer_callback_query(call.id, f"Redirecionando para o suporte: {config.SUPPORT_USERNAME}")
    
    text = f"""🆘 **SUPORTE TÉCNICO**

📞 Entre em contato conosco:

💬 Telegram: {config.SUPPORT_USERNAME}
📧 Email: suporte@joazinhostore.com
⏰ Horário: 24/7

🚀 Resposta rápida garantida!"""

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("⬅️ Voltar", callback_data="back_main"))
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

@bot.callback_query_handler(func=lambda call: call.data == "search")
def request_search(call):
    text = "🔍 Digite o nome do serviço que você procura:"
    
    user_states[call.from_user.id] = "waiting_search"
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id
    )
    
    bot.send_message(
        call.message.chat.id,
        "Digite o nome do serviço:",
        reply_markup=types.ForceReply(selective=True)
    )

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == "waiting_search")
def process_search(message):
    query = message.text.lower()
    
    # Search in sample products
    results = []
    for i, product in enumerate(SAMPLE_PRODUCTS):
        if query in product['name'].lower():
            results.append((i, product))
    
    if not results:
        text = f"❌ Nenhum resultado encontrado para '{message.text}'"
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("⬅️ Voltar", callback_data="back_main"))
    else:
        text = f"🔍 **RESULTADOS DA BUSCA**\n\nEncontrados {len(results)} resultado(s) para '{message.text}':"
        keyboard = types.InlineKeyboardMarkup()
        
        for product_id, product in results:
            keyboard.add(types.InlineKeyboardButton(
                f"{product['name']} - R${product['price']:.2f}",
                callback_data=f"product_{product_id}"
            ))
        
        keyboard.add(types.InlineKeyboardButton("⬅️ Voltar", callback_data="back_main"))
    
    bot.send_message(
        message.chat.id,
        text,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )
    
    user_states[message.from_user.id] = None

@bot.callback_query_handler(func=lambda call: call.data == "back_main")
def back_to_main(call):
    start_command_callback(call)

def start_command_callback(call):
    """Handle start command from callback"""
    user = get_user_data(call.from_user.id)
    
    welcome_text = f"""🥇 Descubra como nosso bot pode transformar sua experiência de compras! Ele facilita a busca por diversos produtos e serviços, garantindo que você encontre o que precisa com o melhor preço e excelente custo-benefício.

Importante: Não realizamos reembolsos em dinheiro. O suporte estará disponível por até 48 horas após a entrega das informações, com reembolso em créditos no bot, se necessário.

👥 Grupo De Clientes: 
{config.CLIENT_GROUP_LINK}

👨🏻‍💻 Link De Suporte: {config.SUPPORT_USERNAME}

ℹ️ Seus Dados:
├🆔 ID: {user.telegram_id}
├💸 Saldo Atual: R${user.balance:.2f}
├🪪 Usuário: {call.from_user.first_name or 'N/A'}

Escolha uma opção:"""

    bot.edit_message_text(
        welcome_text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=create_main_keyboard()
    )

# Command handlers for menu commands
@bot.message_handler(commands=['pix'])
def pix_command(message):
    parts = message.text.split()
    if len(parts) != 2:
        bot.reply_to(message, """Você enviou em um formato incorreto. Envie /pix e o valor que deseja...
Exemplo:
/pix 10
/pix 5.25""")
        return
    
    try:
        amount = float(parts[1].replace(',', '.'))
        if amount < config.MIN_RECHARGE:
            bot.reply_to(message, f"❌ Valor mínimo para recarga é R${config.MIN_RECHARGE:.2f}")
            return
        
        # Process PIX payment (same logic as above)
        process_pix_payment(message, amount)
        
    except ValueError:
        bot.reply_to(message, "❌ Por favor, envie um valor numérico válido.")

def process_pix_payment(message, amount):
    """Process PIX payment"""
    user = get_user_data(message.from_user.id)
    transaction_id = utils.generate_referral_code(user.id) + str(int(datetime.now().timestamp()))[-4:]
    
    pix_code = "00020101021226810014br.gov.bcb.pix2559qr.woovi.com/qr/v2/cob/04f784f1-e7e8-4b92-a31b-97d5dedd28dc520400005303986540529.005802BR5909PushinPay6009Sao_Paulo622905257d6eb598cf4d46abb05fbedd963040E64"
    
    text = f"""Gerando pagamento...
💰 Comprar Saldo com Pix Automático:

⏱️ Expira em: {config.PIX_EXPIRY_MINUTES} Minutos  
💵 Valor: R$ {amount:.2f}  
✨ ID da Recarga: {transaction_id}

📃 Atenção: Este código é válido para apenas um único pagamento.  
Se você utilizá-lo mais de uma vez, o saldo adicional será perdido sem direito a reembolso.

💎 Pix Copia e Cola:  
{pix_code}

💡 Dica: Clique no código acima para copiar.  

🇧🇷 Após o pagamento, seu saldo será liberado instantaneamente."""

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("⏳ Aguardando Pagamento", callback_data=f"check_payment_{transaction_id}"))
    
    bot.send_message(
        message.chat.id,
        text,
        reply_markup=keyboard
    )

@bot.message_handler(commands=['historico'])
def history_command(message):
    user = get_user_data(message.from_user.id)
    
    db = SessionLocal()
    try:
        purchases = db.query(Purchase).filter(Purchase.user_id == user.id).all()
        
        if not purchases:
            text = "Você não tem compras no bot. Quando comprar alguma conta, as informações dela ficarão exibidas aqui."
        else:
            text = "📊 **HISTÓRICO DE COMPRAS**\n\n"
            for purchase in purchases:
                text += f"🛒 {purchase.service.name}\n💰 R${purchase.amount:.2f}\n📅 {purchase.created_at.strftime('%d/%m/%Y %H:%M')}\n\n"
    finally:
        db.close()
    
    bot.send_message(message.chat.id, text, parse_mode='Markdown')

@bot.message_handler(commands=['afiliados'])
def affiliates_command(message):
    user = get_user_data(message.from_user.id)
    referral_link = f"t.me/{bot.get_me().username}?start={user.telegram_id}"
    
    text = f"""◉ ═════ ❈ ═════ ◉  
ℹ️ Status: {'Ativado' if config.AFFILIATE_STATUS else 'Desativado'}  
├📊 Comissão por Indicação: {int(config.AFFILIATE_COMMISSION_RATE * 100)}%
├👥 Total de Afiliados: 0
└🔗 Link para Indicar: {referral_link}  
◉ ═════ ❈ ═════ ◉  

Como Funciona?  
Copie seu link de indicação e envie para outras pessoas.  
Cada vez que alguém indicado por você fizer uma recarga no bot, você receberá uma porcentagem desse valor!  
Por exemplo, com uma comissão de 50%, se 5 pessoas indicadas recarregarem R$10,00 cada, você receberá R$25,00.  

Indique mais e aumente seus ganhos!"""
    
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['id'])
def id_command(message):
    bot.send_message(message.chat.id, f"🆔 Seu id é: {message.from_user.id}")

@bot.message_handler(commands=['saldo'])
def balance_command(message):
    user = get_user_data(message.from_user.id)
    
    text = f"""╭───────────────────╮
💰 Carteira id: {user.telegram_id}
💸 Saldo: {user.balance:.2f}
╰───────────────────╯"""
    
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['ranking'])
def ranking_command(message):
    # Send ranking menu as message with inline keyboard
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.row(
        types.InlineKeyboardButton("🎯 Serviços ✅", callback_data="rank_services"),
        types.InlineKeyboardButton("💰 Recargas", callback_data="rank_recharges")
    )
    keyboard.row(
        types.InlineKeyboardButton("🛒 Compras", callback_data="rank_purchases"),
        types.InlineKeyboardButton("💳 Saldo", callback_data="rank_balance")
    )
    
    text = """🏆 Ranking dos serviços mais vendidos (deste mês)

1°) Premiere (tela) 🥇 - Com 66 pedidos
2°) Globoplay+canais (tela) 🥈 - Com 66 pedidos
3°) Prime video (tela) 🥉 - Com 65 pedidos
4°) Disney+star premium (tela) - Com 40 pedidos
5°) Iptv premium (mensal) - Com 35 pedidos
6°) Max (tela) - Com 28 pedidos
7°) Youtube premium (convite) - Com 25 pedidos
8°) Netflix premium (tela) - Com 23 pedidos
9°) Globoplay+canais+telecine (tela) - Com 20 pedidos
10°) Grupos vips +30 links +18 (acesso) - Com 19 pedidos"""
    
    bot.send_message(message.chat.id, text, reply_markup=keyboard)

@bot.message_handler(commands=['termos'])
def terms_command(message):
    text = f"""NOTIFICAÇÃO PRÉVIA AOS USUÁRIOS

Prezado Usuário, Antes de utilizar os serviços do aplicativo {config.STORE_NAME}, solicitamos sua atenção aos Termos de Uso que regulam a relação entre o Usuário e o desenvolvedor.

Ao utilizar os serviços, o Usuário concorda em se submeter aos Termos de Uso disponíveis em {config.TERMS_URL}, que estabelecem as condições legais da utilização do aplicativo, incluindo políticas de recarga de saldo e limitações de responsabilidade.

O Desenvolvedor não se responsabiliza pelos produtos comercializados no aplicativo nem por usos indevidos. Recomendamos a leitura completa dos Termos para uma compreensão detalhada.

Ao prosseguir com a utilização dos serviços, o Usuário manifesta sua concordância com os Termos estabelecidos. Para uma visão abrangente, acesse a versão completa em {config.TERMS_URL}.

Atenciosamente, Joazinho Store"""
    
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['alertas'])
def alerts_command(message):
    text = """⚠️ Sistema de /alertas

Seja notificado quando seu serviço favorito for abastecido 🤩
🎯 Basta selecionar abaixo os serviços que você deseja ser notificado, e eu lhe avisarei sempre que for abastecido novas unidades.

✅ Nossos produtos são de grandes demandas e acabam rápido, é importante que você seja notificado para aproveitar antes que acabe!

Lista de serviços que você pode ser notificado ⤵️"""

    keyboard = types.InlineKeyboardMarkup()
    
    # Add alert toggles for each product
    for i, product in enumerate(SAMPLE_PRODUCTS):
        # For now, all are disabled (❌), in real implementation check user preferences
        keyboard.add(types.InlineKeyboardButton(
            f"❌ {product['name']}",
            callback_data=f"toggle_alert_{i}"
        ))
    
    bot.send_message(message.chat.id, text, reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("toggle_alert_"))
def toggle_alert(call):
    # Toggle alert for specific product
    bot.answer_callback_query(call.id, "Alerta alternado!")
    # In real implementation, update user preferences in database

if __name__ == "__main__":
    print("Store bot started...")
    bot.polling(none_stop=True)