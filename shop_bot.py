import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode
import io
import base64
from config import SHOP_BOT_TOKEN, MESSAGES, CATEGORY_EMOJIS, MIN_RECHARGE_AMOUNT, MAX_RECHARGE_AMOUNT
from database import db
from payment_system import payment_system
import json
from datetime import datetime, timedelta

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class ShopBot:
    def __init__(self):
        self.application = None
        self.user_states = {}
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start do bot da loja"""
        user = update.effective_user
        
        # Conectar ao banco de dados
        if not db.connection or not db.connection.is_connected():
            db.connect()
        
        # Verificar se o usuário existe, se não, criar
        existing_user = db.get_user(user.id)
        if not existing_user:
            # Verificar se há referral
            referrer_id = None
            if context.args and context.args[0].startswith('ref_'):
                try:
                    referrer_id = int(context.args[0].replace('ref_', ''))
                except:
                    pass
            
            db.create_user(
                user_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                referrer_id=referrer_id
            )
            
            # Log de novo usuário
            db.add_log(user.id, "user_registered", f"Novo usuário registrado: {user.first_name}")
        
        await self.show_main_menu(update, context)
    
    async def show_main_menu(self, update_or_query, context=None, edit=False):
        """Mostra o menu principal da loja"""
        if hasattr(update_or_query, 'effective_user'):
            user = update_or_query.effective_user
            chat = update_or_query.effective_chat
        else:
            user = update_or_query.from_user
            chat = update_or_query.message.chat
        
        # Buscar dados do usuário
        user_data = db.get_user(user.id)
        balance = user_data['balance'] if user_data else 0.0
        
        keyboard = [
            [InlineKeyboardButton("🛍️ Logins | Contas Premium", callback_data="shop_categories")],
            [InlineKeyboardButton("👤 Meu Perfil", callback_data="profile"), 
             InlineKeyboardButton("💰 Recarga", callback_data="recharge")],
            [InlineKeyboardButton("🔍 Pesquisar Serviço", callback_data="search_service"),
             InlineKeyboardButton("❓ Suporte", callback_data="support")],
            [InlineKeyboardButton("👥 Sistema de Afiliados", callback_data="affiliate")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_text = f"""🎯 **Bem-vindo à Loja de Contas Premium!**

Olá, {user.first_name}! 👋

💰 **Seu saldo atual:** R$ {balance:.2f}

🌟 **O que você pode fazer:**
• Comprar contas premium de diversos serviços
• Recarregar seu saldo via PIX
• Indicar amigos e ganhar comissões
• Acompanhar seu histórico de compras

Escolha uma opção abaixo para começar:"""
        
        if edit and hasattr(update_or_query, 'edit_message_text'):
            await update_or_query.edit_message_text(welcome_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        else:
            if hasattr(update_or_query, 'message'):
                await update_or_query.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
            else:
                await chat.send_message(welcome_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Processa callbacks dos botões"""
        query = update.callback_query
        user_id = query.from_user.id
        data = query.data
        
        await query.answer()
        
        # Log da ação
        db.add_log(user_id, "button_click", f"Botão clicado: {data}")
        
        if data == "shop_categories":
            await self.show_categories(query)
        elif data == "profile":
            await self.show_profile(query)
        elif data == "recharge":
            await self.show_recharge_menu(query)
        elif data == "search_service":
            await self.show_search_menu(query)
        elif data == "support":
            await self.show_support(query)
        elif data == "affiliate":
            await self.show_affiliate_menu(query)
        elif data == "back_main":
            await self.show_main_menu(query, edit=True)
        elif data.startswith("category_"):
            await self.show_category_services(query, data)
        elif data.startswith("service_"):
            await self.show_service_details(query, data)
        elif data.startswith("buy_"):
            await self.process_purchase(query, data)
        elif data.startswith("recharge_"):
            await self.process_recharge(query, data)
        elif data.startswith("confirm_"):
            await self.confirm_action(query, data)
    
    async def show_categories(self, query):
        """Mostra categorias de serviços"""
        categories = db.get_categories(active_only=True)
        
        if not categories:
            keyboard = [[InlineKeyboardButton("⬅️ Voltar ao Menu", callback_data="back_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            text = "❌ **Nenhuma categoria disponível no momento.**\n\nTente novamente mais tarde."
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
            return
        
        keyboard = []
        for category in categories:
            # Contar serviços disponíveis na categoria
            services = db.get_services_by_category(category['id'], active_only=True)
            available_count = sum(1 for service in services if service['available_stock'] > 0)
            
            if available_count > 0:
                keyboard.append([InlineKeyboardButton(
                    f"{category['emoji']} {category['name']} ({available_count} disponíveis)",
                    callback_data=f"category_{category['id']}"
                )])
        
        keyboard.append([InlineKeyboardButton("⬅️ Voltar ao Menu", callback_data="back_main")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = """🛍️ **Categorias de Serviços**

Escolha uma categoria para ver os serviços disponíveis:"""
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def show_category_services(self, query, data):
        """Mostra serviços de uma categoria"""
        category_id = int(data.replace("category_", ""))
        services = db.get_services_by_category(category_id, active_only=True)
        
        # Filtrar apenas serviços com estoque
        available_services = [s for s in services if s['available_stock'] > 0]
        
        if not available_services:
            keyboard = [
                [InlineKeyboardButton("⬅️ Voltar às Categorias", callback_data="shop_categories")],
                [InlineKeyboardButton("🏠 Menu Principal", callback_data="back_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            text = "❌ **Nenhum serviço disponível nesta categoria no momento.**\n\nTente novamente mais tarde."
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
            return
        
        keyboard = []
        for service in available_services:
            stock_emoji = "🟢" if service['available_stock'] > 10 else "🟡" if service['available_stock'] > 5 else "🔴"
            keyboard.append([InlineKeyboardButton(
                f"{stock_emoji} {service['name']} - R$ {service['price']:.2f} ({service['available_stock']} disponíveis)",
                callback_data=f"service_{service['id']}"
            )])
        
        keyboard.append([InlineKeyboardButton("⬅️ Voltar às Categorias", callback_data="shop_categories")])
        keyboard.append([InlineKeyboardButton("🏠 Menu Principal", callback_data="back_main")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        category_info = available_services[0]  # Pegar info da categoria do primeiro serviço
        text = f"""{category_info['category_emoji']} **{category_info['category_name']}**

Serviços disponíveis:

🟢 Estoque alto (10+)
🟡 Estoque médio (6-10)
🔴 Estoque baixo (1-5)

Clique em um serviço para ver detalhes:"""
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def show_service_details(self, query, data):
        """Mostra detalhes de um serviço"""
        service_id = int(data.replace("service_", ""))
        service = db.get_service(service_id)
        
        if not service or not service['is_active'] or service['available_stock'] == 0:
            keyboard = [[InlineKeyboardButton("⬅️ Voltar", callback_data="shop_categories")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            text = "❌ **Serviço indisponível**\n\nEste serviço não está mais disponível."
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
            return
        
        user_data = db.get_user(query.from_user.id)
        user_balance = user_data['balance'] if user_data else 0.0
        
        can_buy = user_balance >= service['price']
        
        keyboard = []
        if can_buy:
            keyboard.append([InlineKeyboardButton("💳 Comprar Agora", callback_data=f"buy_{service['id']}")])
        else:
            keyboard.append([InlineKeyboardButton("💰 Recarregar Saldo", callback_data="recharge")])
        
        keyboard.append([InlineKeyboardButton("⬅️ Voltar", callback_data=f"category_{service['category_id']}")])
        keyboard.append([InlineKeyboardButton("🏠 Menu Principal", callback_data="back_main")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        warranty_text = f"🛡️ **Garantia:** {service['warranty_days']} dias" if service['warranty_days'] > 0 else ""
        balance_status = "✅ Saldo suficiente" if can_buy else "❌ Saldo insuficiente"
        
        text = f"""{service['category_emoji']} **{service['name']}**

📝 **Descrição:**
{service['description'] or 'Conta premium do serviço.'}

💰 **Preço:** R$ {service['price']:.2f}
📦 **Estoque:** {service['available_stock']} unidades
{warranty_text}

👤 **Seu saldo:** R$ {user_balance:.2f}
{balance_status}"""
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def process_purchase(self, query, data):
        """Processa a compra de um serviço"""
        service_id = int(data.replace("buy_", ""))
        user_id = query.from_user.id
        
        service = db.get_service(service_id)
        if not service or service['available_stock'] == 0:
            await query.answer("❌ Serviço indisponível!", show_alert=True)
            return
        
        # Processar compra
        result = payment_system.create_purchase_transaction(user_id, service_id, service['price'])
        
        if result['success']:
            # Enviar dados da conta
            keyboard = [[InlineKeyboardButton("🏠 Menu Principal", callback_data="back_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            text = f"""✅ **Compra Realizada com Sucesso!**

🛍️ **Produto:** {service['name']}
💰 **Valor:** R$ {service['price']:.2f}

📋 **Dados da Conta:**
```
{result['account_data']}
```

🛡️ **Importante:**
• Guarde estes dados em local seguro
• Em caso de problemas, entre em contato com o suporte
• Garantia de {service['warranty_days']} dias (se aplicável)

Obrigado pela sua compra! 🎉"""
            
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
            
        else:
            await query.answer(f"❌ {result['error']}", show_alert=True)
    
    async def show_profile(self, query):
        """Mostra perfil do usuário"""
        user_data = db.get_user(query.from_user.id)
        
        if not user_data:
            await query.answer("❌ Erro ao carregar perfil!", show_alert=True)
            return
        
        # Buscar estatísticas do usuário
        transactions = db.get_user_transactions(query.from_user.id, limit=5)
        
        # Calcular total gasto
        cursor = db.connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT SUM(amount) as total_spent, COUNT(*) as total_purchases
            FROM transactions 
            WHERE user_id = %s AND type = 'purchase' AND payment_status = 'approved'
        """, (query.from_user.id,))
        stats = cursor.fetchone()
        
        total_spent = stats['total_spent'] or 0
        total_purchases = stats['total_purchases'] or 0
        
        # Buscar indicados
        cursor.execute("SELECT COUNT(*) as total_referrals FROM users WHERE referrer_id = %s", (query.from_user.id,))
        referrals = cursor.fetchone()['total_referrals']
        
        keyboard = [
            [InlineKeyboardButton("📊 Histórico Completo", callback_data="profile_history")],
            [InlineKeyboardButton("👥 Meus Indicados", callback_data="profile_referrals")],
            [InlineKeyboardButton("⬅️ Voltar ao Menu", callback_data="back_main")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        member_since = user_data['created_at'].strftime("%d/%m/%Y")
        
        text = f"""👤 **Meu Perfil**

👋 **Nome:** {user_data['first_name']}
🆔 **ID:** {user_data['user_id']}
📅 **Membro desde:** {member_since}

💰 **Financeiro:**
• Saldo atual: R$ {user_data['balance']:.2f}
• Total gasto: R$ {total_spent:.2f}
• Compras realizadas: {total_purchases}

👥 **Afiliados:**
• Indicados: {referrals} pessoas

📋 **Últimas transações:**"""
        
        if transactions:
            for trans in transactions[:3]:
                date = trans['created_at'].strftime("%d/%m")
                trans_type = {"purchase": "🛍️ Compra", "recharge": "💰 Recarga", "commission": "💸 Comissão"}
                text += f"\n• {date} - {trans_type.get(trans['type'], trans['type'])}: R$ {trans['amount']:.2f}"
        else:
            text += "\n• Nenhuma transação encontrada"
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def show_recharge_menu(self, query):
        """Mostra menu de recarga"""
        keyboard = [
            [InlineKeyboardButton("💰 R$ 10,00", callback_data="recharge_10"),
             InlineKeyboardButton("💰 R$ 25,00", callback_data="recharge_25")],
            [InlineKeyboardButton("💰 R$ 50,00", callback_data="recharge_50"),
             InlineKeyboardButton("💰 R$ 100,00", callback_data="recharge_100")],
            [InlineKeyboardButton("💰 Valor Personalizado", callback_data="recharge_custom")],
            [InlineKeyboardButton("⬅️ Voltar ao Menu", callback_data="back_main")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = f"""💰 **Recarregar Saldo**

Escolha o valor que deseja recarregar:

💳 **Pagamento via PIX**
• Pagamento instantâneo
• QR Code gerado automaticamente
• Saldo creditado em até 5 minutos

💡 **Valores sugeridos:**"""
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def process_recharge(self, query, data):
        """Processa recarga de saldo"""
        user_id = query.from_user.id
        
        # Extrair valor da recarga
        if data == "recharge_custom":
            # Implementar entrada de valor personalizado
            self.user_states[user_id] = {"action": "waiting_custom_amount"}
            
            keyboard = [[InlineKeyboardButton("❌ Cancelar", callback_data="recharge")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            text = f"""💰 **Valor Personalizado**

Digite o valor que deseja recarregar:

💡 **Limites:**
• Mínimo: R$ {MIN_RECHARGE_AMOUNT:.2f}
• Máximo: R$ {MAX_RECHARGE_AMOUNT:.2f}

Digite apenas o número (exemplo: 75.50):"""
            
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
            return
        
        amount_map = {
            "recharge_10": 10.00,
            "recharge_25": 25.00,
            "recharge_50": 50.00,
            "recharge_100": 100.00
        }
        
        amount = amount_map.get(data)
        if not amount:
            await query.answer("❌ Valor inválido!", show_alert=True)
            return
        
        # Criar pagamento PIX
        payment_result = payment_system.create_pix_payment(user_id, amount)
        
        if payment_result['success']:
            # Mostrar QR Code
            keyboard = [
                [InlineKeyboardButton("🔄 Verificar Pagamento", callback_data=f"check_payment_{payment_result['payment_id']}")],
                [InlineKeyboardButton("❌ Cancelar", callback_data="recharge")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Converter QR Code base64 para imagem
            if payment_result['qr_code_base64']:
                qr_image = io.BytesIO(base64.b64decode(payment_result['qr_code_base64']))
                qr_image.seek(0)
                
                text = f"""💳 **Pagamento PIX Gerado**

💰 **Valor:** R$ {amount:.2f}
⏰ **Válido até:** 30 minutos

📱 **Como pagar:**
1. Abra seu app bancário
2. Escaneie o QR Code abaixo
3. Confirme o pagamento
4. Aguarde a confirmação (até 5 min)

🔄 Use o botão abaixo para verificar se o pagamento foi aprovado."""
                
                await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
                await query.message.reply_photo(photo=qr_image, caption="📱 **QR Code PIX**\n\nEscaneie com seu app bancário")
            else:
                text = f"""💳 **Pagamento PIX Gerado**

💰 **Valor:** R$ {amount:.2f}
⏰ **Válido até:** 30 minutos

📋 **Código PIX Copia e Cola:**
```
{payment_result['qr_code']}
```

🔄 Use o botão abaixo para verificar se o pagamento foi aprovado."""
                
                await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        else:
            await query.answer(f"❌ {payment_result['error']}", show_alert=True)
    
    async def show_support(self, query):
        """Mostra informações de suporte"""
        keyboard = [[InlineKeyboardButton("⬅️ Voltar ao Menu", callback_data="back_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = """❓ **Suporte Técnico**

🕐 **Horário de Atendimento:**
• Segunda a Sexta: 9h às 18h
• Sábado: 9h às 14h
• Domingo: Fechado

📞 **Contatos:**
• Telegram: @suporte_bot
• WhatsApp: +55 11 99999-9999
• Email: suporte@loja.com

🔧 **Problemas Comuns:**
• Login não funciona? Entre em contato em até 24h
• Pagamento não processado? Aguarde até 30 minutos
• Conta com problema? Temos garantia!

💡 **Dica:** Sempre guarde o comprovante da sua compra!"""
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def show_affiliate_menu(self, query):
        """Mostra menu do sistema de afiliados"""
        user_id = query.from_user.id
        
        # Buscar dados de afiliado
        cursor = db.connection.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) as total_referrals FROM users WHERE referrer_id = %s", (user_id,))
        total_referrals = cursor.fetchone()['total_referrals']
        
        cursor.execute("""
            SELECT SUM(amount) as total_commission 
            FROM commissions 
            WHERE referrer_id = %s AND is_paid = TRUE
        """, (user_id,))
        total_commission = cursor.fetchone()['total_commission'] or 0
        
        # Link de indicação
        referral_link = f"https://t.me/{context.bot.username}?start=ref_{user_id}"
        
        keyboard = [
            [InlineKeyboardButton("📊 Meus Indicados", callback_data="affiliate_referrals")],
            [InlineKeyboardButton("💰 Histórico de Comissões", callback_data="affiliate_commissions")],
            [InlineKeyboardButton("⬅️ Voltar ao Menu", callback_data="back_main")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = f"""👥 **Sistema de Afiliados**

💰 **Ganhe 50% de comissão** em todas as recargas dos seus indicados!

📊 **Suas estatísticas:**
• Indicados: {total_referrals} pessoas
• Comissão total: R$ {total_commission:.2f}

🔗 **Seu link de indicação:**
```
{referral_link}
```

📋 **Como funciona:**
1. Compartilhe seu link
2. Pessoas se cadastram pelo seu link
3. Você ganha 50% de cada recarga que elas fizerem
4. Comissão é creditada automaticamente

💡 **Dica:** Compartilhe em grupos, redes sociais e com amigos!"""
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Processa mensagens de texto"""
        user_id = update.effective_user.id
        text = update.message.text
        
        user_state = self.user_states.get(user_id, {})
        
        if user_state.get('action') == 'waiting_custom_amount':
            try:
                amount = float(text.replace(',', '.'))
                
                if amount < MIN_RECHARGE_AMOUNT or amount > MAX_RECHARGE_AMOUNT:
                    await update.message.reply_text(
                        f"❌ **Valor inválido!**\n\nO valor deve estar entre R$ {MIN_RECHARGE_AMOUNT:.2f} e R$ {MAX_RECHARGE_AMOUNT:.2f}",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return
                
                # Limpar estado
                del self.user_states[user_id]
                
                # Processar recarga
                payment_result = payment_system.create_pix_payment(user_id, amount)
                
                if payment_result['success']:
                    keyboard = [
                        [InlineKeyboardButton("🔄 Verificar Pagamento", callback_data=f"check_payment_{payment_result['payment_id']}")],
                        [InlineKeyboardButton("❌ Cancelar", callback_data="recharge")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    if payment_result['qr_code_base64']:
                        qr_image = io.BytesIO(base64.b64decode(payment_result['qr_code_base64']))
                        qr_image.seek(0)
                        
                        text = f"""💳 **Pagamento PIX Gerado**

💰 **Valor:** R$ {amount:.2f}
⏰ **Válido até:** 30 minutos

📱 **Como pagar:**
1. Abra seu app bancário
2. Escaneie o QR Code abaixo
3. Confirme o pagamento
4. Aguarde a confirmação (até 5 min)"""
                        
                        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
                        await update.message.reply_photo(photo=qr_image, caption="📱 **QR Code PIX**")
                    else:
                        text = f"""💳 **Pagamento PIX Gerado**

💰 **Valor:** R$ {amount:.2f}
⏰ **Válido até:** 30 minutos

📋 **Código PIX:**
```
{payment_result['qr_code']}
```"""
                        
                        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
                else:
                    await update.message.reply_text(f"❌ {payment_result['error']}")
                
            except ValueError:
                await update.message.reply_text(
                    "❌ **Valor inválido!**\n\nDigite apenas números (exemplo: 75.50)",
                    parse_mode=ParseMode.MARKDOWN
                )
    
    def run(self):
        """Inicia o bot da loja"""
        # Conectar ao banco de dados
        if db.connect():
            db.create_tables()
        
        # Criar aplicação
        self.application = Application.builder().token(SHOP_BOT_TOKEN).build()
        
        # Adicionar handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Iniciar bot
        logger.info("Bot da loja iniciado!")
        self.application.run_polling()

if __name__ == "__main__":
    shop_bot = ShopBot()
    shop_bot.run()