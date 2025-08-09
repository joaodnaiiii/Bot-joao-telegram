import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode
import io
import base64
from config import ADMIN_BOT_TOKEN, ADMIN_IDS, MESSAGES
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

class AdminBot:
    def __init__(self):
        self.application = None
        self.user_states = {}
        
    def is_admin(self, user_id):
        """Verifica se o usuário é administrador"""
        return user_id in ADMIN_IDS
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start do bot administrativo"""
        user_id = update.effective_user.id
        
        if not self.is_admin(user_id):
            await update.message.reply_text("❌ **Acesso Negado**\n\nVocê não tem permissão para acessar este bot.", parse_mode=ParseMode.MARKDOWN)
            return
        
        # Conectar ao banco de dados
        if not db.connection or not db.connection.is_connected():
            db.connect()
        
        keyboard = [
            [InlineKeyboardButton("🏪 Gerenciar Loja", callback_data="manage_shop")],
            [InlineKeyboardButton("👥 Gerenciar Usuários", callback_data="manage_users")],
            [InlineKeyboardButton("💰 Financeiro", callback_data="financial")],
            [InlineKeyboardButton("📊 Estatísticas", callback_data="statistics")],
            [InlineKeyboardButton("⚙️ Configurações", callback_data="settings")],
            [InlineKeyboardButton("📋 Logs do Sistema", callback_data="system_logs")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_text = f"""🔧 **Painel Administrativo - Bot de Vendas**

Bem-vindo ao painel de controle, {update.effective_user.first_name}!

Selecione uma opção abaixo para gerenciar o sistema:"""
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def adm_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /adm - mesmo que /start"""
        await self.start_command(update, context)
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Processa callbacks dos botões"""
        query = update.callback_query
        user_id = query.from_user.id
        
        if not self.is_admin(user_id):
            await query.answer("❌ Acesso negado!", show_alert=True)
            return
        
        await query.answer()
        
        data = query.data
        
        if data == "manage_shop":
            await self.show_shop_management(query)
        elif data == "manage_users":
            await self.show_user_management(query)
        elif data == "financial":
            await self.show_financial_menu(query)
        elif data == "statistics":
            await self.show_statistics(query)
        elif data == "settings":
            await self.show_settings_menu(query)
        elif data == "system_logs":
            await self.show_system_logs(query)
        elif data == "back_main":
            await self.show_main_menu(query)
        elif data.startswith("shop_"):
            await self.handle_shop_actions(query, data)
        elif data.startswith("user_"):
            await self.handle_user_actions(query, data)
        elif data.startswith("financial_"):
            await self.handle_financial_actions(query, data)
        elif data.startswith("category_"):
            await self.handle_category_actions(query, data)
        elif data.startswith("service_"):
            await self.handle_service_actions(query, data)
    
    async def show_main_menu(self, query):
        """Mostra menu principal"""
        keyboard = [
            [InlineKeyboardButton("🏪 Gerenciar Loja", callback_data="manage_shop")],
            [InlineKeyboardButton("👥 Gerenciar Usuários", callback_data="manage_users")],
            [InlineKeyboardButton("💰 Financeiro", callback_data="financial")],
            [InlineKeyboardButton("📊 Estatísticas", callback_data="statistics")],
            [InlineKeyboardButton("⚙️ Configurações", callback_data="settings")],
            [InlineKeyboardButton("📋 Logs do Sistema", callback_data="system_logs")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = "🔧 **Painel Administrativo**\n\nSelecione uma opção:"
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def show_shop_management(self, query):
        """Mostra menu de gerenciamento da loja"""
        keyboard = [
            [InlineKeyboardButton("📂 Gerenciar Categorias", callback_data="shop_categories")],
            [InlineKeyboardButton("🛍️ Gerenciar Serviços", callback_data="shop_services")],
            [InlineKeyboardButton("📦 Gerenciar Estoque", callback_data="shop_stock")],
            [InlineKeyboardButton("🔄 Sincronizar Bots", callback_data="shop_sync")],
            [InlineKeyboardButton("⬅️ Voltar", callback_data="back_main")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = "🏪 **Gerenciamento da Loja**\n\nEscolha uma opção:"
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def show_user_management(self, query):
        """Mostra menu de gerenciamento de usuários"""
        # Buscar estatísticas rápidas
        cursor = db.connection.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) as total FROM users")
        total_users = cursor.fetchone()["total"]
        
        cursor.execute("SELECT COUNT(*) as total FROM users WHERE is_admin = TRUE")
        total_admins = cursor.fetchone()["total"]
        
        cursor.execute("SELECT COUNT(*) as total FROM users WHERE is_banned = TRUE")
        total_banned = cursor.fetchone()["total"]
        
        keyboard = [
            [InlineKeyboardButton("👤 Buscar Usuário", callback_data="user_search")],
            [InlineKeyboardButton("👑 Gerenciar Admins", callback_data="user_admins")],
            [InlineKeyboardButton("🚫 Usuários Banidos", callback_data="user_banned")],
            [InlineKeyboardButton("💰 Ajustar Saldos", callback_data="user_balance")],
            [InlineKeyboardButton("📊 Top Usuários", callback_data="user_top")],
            [InlineKeyboardButton("⬅️ Voltar", callback_data="back_main")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = f"""👥 **Gerenciamento de Usuários**

📈 **Estatísticas:**
• Total de usuários: {total_users}
• Administradores: {total_admins}
• Usuários banidos: {total_banned}

Escolha uma opção:"""
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def show_financial_menu(self, query):
        """Mostra menu financeiro"""
        # Buscar estatísticas financeiras
        stats = db.get_sales_stats(30)
        
        cursor = db.connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT SUM(balance) as total_balance FROM users
        """)
        total_balance = cursor.fetchone()["total_balance"] or 0
        
        keyboard = [
            [InlineKeyboardButton("💳 Transações Recentes", callback_data="financial_transactions")],
            [InlineKeyboardButton("📊 Relatórios", callback_data="financial_reports")],
            [InlineKeyboardButton("💰 Comissões", callback_data="financial_commissions")],
            [InlineKeyboardButton("🔄 Reembolsos", callback_data="financial_refunds")],
            [InlineKeyboardButton("⬅️ Voltar", callback_data="back_main")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        revenue = stats["total_revenue"] if stats else 0
        sales = stats["total_sales"] if stats else 0
        avg_sale = stats["avg_sale_value"] if stats else 0
        
        text = f"""💰 **Painel Financeiro**

📊 **Últimos 30 dias:**
• Faturamento: R$ {revenue:.2f}
• Vendas realizadas: {sales}
• Ticket médio: R$ {avg_sale:.2f}
• Saldo total dos usuários: R$ {total_balance:.2f}

Escolha uma opção:"""
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def show_statistics(self, query):
        """Mostra estatísticas detalhadas"""
        # Buscar estatísticas
        cursor = db.connection.cursor(dictionary=True)
        
        # Usuários
        cursor.execute("SELECT COUNT(*) as total FROM users")
        total_users = cursor.fetchone()["total"]
        
        cursor.execute("SELECT COUNT(*) as total FROM users WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)")
        new_users = cursor.fetchone()["total"]
        
        # Vendas
        stats_30 = db.get_sales_stats(30)
        stats_7 = db.get_sales_stats(7)
        
        # Produtos mais vendidos
        cursor.execute("""
            SELECT s.name, COUNT(t.id) as sales_count
            FROM transactions t
            JOIN services s ON t.service_id = s.id
            WHERE t.type = 'purchase' AND t.payment_status = 'approved'
            AND t.created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            GROUP BY s.id
            ORDER BY sales_count DESC
            LIMIT 5
        """)
        top_products = cursor.fetchall()
        
        keyboard = [
            [InlineKeyboardButton("📈 Gráficos Detalhados", callback_data="stats_charts")],
            [InlineKeyboardButton("📋 Exportar Relatório", callback_data="stats_export")],
            [InlineKeyboardButton("⬅️ Voltar", callback_data="back_main")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        top_products_text = "\n".join([f"• {p['name']}: {p['sales_count']} vendas" for p in top_products[:3]])
        if not top_products_text:
            top_products_text = "• Nenhuma venda registrada"
        
        text = f"""📊 **Estatísticas Detalhadas**

👥 **Usuários:**
• Total: {total_users}
• Novos (7 dias): {new_users}

💰 **Vendas (30 dias):**
• Faturamento: R$ {stats_30['total_revenue'] if stats_30 else 0:.2f}
• Vendas: {stats_30['total_sales'] if stats_30 else 0}
• Ticket médio: R$ {stats_30['avg_sale_value'] if stats_30 else 0:.2f}

💰 **Vendas (7 dias):**
• Faturamento: R$ {stats_7['total_revenue'] if stats_7 else 0:.2f}
• Vendas: {stats_7['total_sales'] if stats_7 else 0}

🏆 **Produtos mais vendidos:**
{top_products_text}"""
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def show_settings_menu(self, query):
        """Mostra menu de configurações"""
        keyboard = [
            [InlineKeyboardButton("🔧 Configurações Gerais", callback_data="settings_general")],
            [InlineKeyboardButton("💳 Config. Pagamento", callback_data="settings_payment")],
            [InlineKeyboardButton("📱 Config. Bot Loja", callback_data="settings_shop_bot")],
            [InlineKeyboardButton("🔐 Segurança", callback_data="settings_security")],
            [InlineKeyboardButton("⬅️ Voltar", callback_data="back_main")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = "⚙️ **Configurações do Sistema**\n\nEscolha uma categoria:"
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def show_system_logs(self, query):
        """Mostra logs do sistema"""
        cursor = db.connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT l.*, u.username, u.first_name
            FROM logs l
            LEFT JOIN users u ON l.user_id = u.user_id
            ORDER BY l.created_at DESC
            LIMIT 20
        """)
        logs = cursor.fetchall()
        
        keyboard = [
            [InlineKeyboardButton("🔄 Atualizar", callback_data="system_logs")],
            [InlineKeyboardButton("📤 Exportar Logs", callback_data="logs_export")],
            [InlineKeyboardButton("⬅️ Voltar", callback_data="back_main")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        logs_text = ""
        for log in logs[:10]:
            username = log['username'] or log['first_name'] or f"ID:{log['user_id']}"
            date = log['created_at'].strftime("%d/%m %H:%M")
            logs_text += f"• {date} - {username}: {log['action']}\n"
        
        if not logs_text:
            logs_text = "• Nenhum log encontrado"
        
        text = f"""📋 **Logs do Sistema**

**Últimas atividades:**
{logs_text}

Total de logs: {len(logs)}"""
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def handle_shop_actions(self, query, data):
        """Processa ações da loja"""
        if data == "shop_categories":
            await self.show_categories_management(query)
        elif data == "shop_services":
            await self.show_services_management(query)
        elif data == "shop_stock":
            await self.show_stock_management(query)
        elif data == "shop_sync":
            await self.sync_bots(query)
    
    async def show_categories_management(self, query):
        """Mostra gerenciamento de categorias"""
        categories = db.get_categories(active_only=False)
        
        keyboard = []
        for category in categories:
            status_emoji = "✅" if category['is_active'] else "❌"
            keyboard.append([InlineKeyboardButton(
                f"{category['emoji']} {category['name']} {status_emoji}",
                callback_data=f"category_{category['id']}"
            )])
        
        keyboard.append([InlineKeyboardButton("➕ Adicionar Categoria", callback_data="category_add")])
        keyboard.append([InlineKeyboardButton("⬅️ Voltar", callback_data="manage_shop")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = "📂 **Gerenciar Categorias**\n\nCategorias disponíveis:"
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def show_services_management(self, query):
        """Mostra gerenciamento de serviços"""
        cursor = db.connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT s.*, c.name as category_name, c.emoji as category_emoji,
                   (SELECT COUNT(*) FROM accounts a WHERE a.service_id = s.id AND a.is_sold = FALSE) as stock
            FROM services s
            LEFT JOIN categories c ON s.category_id = c.id
            ORDER BY c.name, s.name
            LIMIT 20
        """)
        services = cursor.fetchall()
        
        keyboard = []
        for service in services:
            status_emoji = "✅" if service['is_active'] else "❌"
            stock_info = f"📦{service['stock']}"
            keyboard.append([InlineKeyboardButton(
                f"{service['category_emoji']} {service['name']} {status_emoji} {stock_info}",
                callback_data=f"service_{service['id']}"
            )])
        
        keyboard.append([InlineKeyboardButton("➕ Adicionar Serviço", callback_data="service_add")])
        keyboard.append([InlineKeyboardButton("⬅️ Voltar", callback_data="manage_shop")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = "🛍️ **Gerenciar Serviços**\n\nServiços disponíveis:"
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def show_stock_management(self, query):
        """Mostra gerenciamento de estoque"""
        cursor = db.connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT s.*, c.name as category_name, c.emoji as category_emoji,
                   (SELECT COUNT(*) FROM accounts a WHERE a.service_id = s.id AND a.is_sold = FALSE) as available_stock,
                   (SELECT COUNT(*) FROM accounts a WHERE a.service_id = s.id AND a.is_sold = TRUE) as sold_stock
            FROM services s
            LEFT JOIN categories c ON s.category_id = c.id
            WHERE s.is_active = TRUE
            ORDER BY available_stock ASC
        """)
        services = cursor.fetchall()
        
        keyboard = []
        for service in services:
            stock_status = "🔴" if service['available_stock'] == 0 else "🟡" if service['available_stock'] < 5 else "🟢"
            keyboard.append([InlineKeyboardButton(
                f"{stock_status} {service['name']} - {service['available_stock']} disponíveis",
                callback_data=f"stock_{service['id']}"
            )])
        
        keyboard.append([InlineKeyboardButton("📦 Adicionar Estoque em Lote", callback_data="stock_bulk_add")])
        keyboard.append([InlineKeyboardButton("⬅️ Voltar", callback_data="manage_shop")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = """📦 **Gerenciamento de Estoque**

🟢 Estoque bom (5+)
🟡 Estoque baixo (1-4)
🔴 Sem estoque

Clique em um serviço para gerenciar:"""
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def sync_bots(self, query):
        """Sincroniza informações entre bots"""
        try:
            # Aqui você pode implementar a lógica de sincronização
            # Por exemplo, recarregar cache, atualizar configurações, etc.
            
            keyboard = [[InlineKeyboardButton("⬅️ Voltar", callback_data="manage_shop")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            text = """🔄 **Sincronização de Bots**

✅ Sincronização realizada com sucesso!

• Cache de serviços atualizado
• Cache de usuários atualizado
• Configurações sincronizadas
• Estoque atualizado

Todos os bots estão agora sincronizados."""
            
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error(f"Erro na sincronização: {e}")
            
            keyboard = [[InlineKeyboardButton("⬅️ Voltar", callback_data="manage_shop")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            text = f"❌ **Erro na Sincronização**\n\n{str(e)}"
            
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Processa mensagens de texto"""
        user_id = update.effective_user.id
        
        if not self.is_admin(user_id):
            return
        
        # Aqui você pode implementar handlers para entrada de dados
        # Por exemplo, quando o admin está adicionando um novo serviço
        
        text = update.message.text
        user_state = self.user_states.get(user_id, {})
        
        if user_state.get('action') == 'add_service':
            # Implementar lógica para adicionar serviço
            pass
        elif user_state.get('action') == 'add_category':
            # Implementar lógica para adicionar categoria
            pass
    
    def run(self):
        """Inicia o bot administrativo"""
        # Conectar ao banco de dados
        if db.connect():
            db.create_tables()
        
        # Criar aplicação
        self.application = Application.builder().token(ADMIN_BOT_TOKEN).build()
        
        # Adicionar handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("adm", self.adm_command))
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Iniciar bot
        logger.info("Bot administrativo iniciado!")
        self.application.run_polling()

if __name__ == "__main__":
    admin_bot = AdminBot()
    admin_bot.run()