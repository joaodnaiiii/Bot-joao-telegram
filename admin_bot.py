import logging
import asyncio
import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from database import db
from payment_system import pix_system
import json
from datetime import datetime
import io
import base64

load_dotenv()

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

class AdminBot:
    def __init__(self):
        self.token = os.getenv('ADMIN_BOT_TOKEN')
        self.admin_password = os.getenv('ADMIN_PASSWORD')
        self.main_admin_id = int(os.getenv('MAIN_ADMIN_ID', 0))
        self.application = None
        self.user_states = {}
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start - Menu principal do admin"""
        user_id = update.effective_user.id
        
        # Verificar se é admin
        if not self.is_admin(user_id):
            await update.message.reply_text(
                "🔐 *Acesso Restrito*\n\n"
                "Este bot é exclusivo para administradores.\n"
                "Digite a senha de administrador:",
                parse_mode='Markdown'
            )
            self.user_states[user_id] = 'awaiting_password'
            return
        
        # Registrar usuário no banco se não existir
        db.create_user(
            user_id=user_id,
            username=update.effective_user.username,
            first_name=update.effective_user.first_name
        )
        
        await self.show_main_menu(update, context)
    
    async def admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /adm - Acesso direto ao painel admin"""
        await self.start_command(update, context)
    
    def is_admin(self, user_id):
        """Verifica se o usuário é administrador"""
        if user_id == self.main_admin_id:
            return True
        admin = db.is_admin(user_id)
        return admin is not None
    
    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Exibe o menu principal do administrador"""
        keyboard = [
            [
                InlineKeyboardButton("🛍️ Gerenciar Serviços", callback_data="manage_services"),
                InlineKeyboardButton("👥 Gerenciar Usuários", callback_data="manage_users")
            ],
            [
                InlineKeyboardButton("📊 Relatórios", callback_data="reports"),
                InlineKeyboardButton("💰 Pagamentos", callback_data="payments")
            ],
            [
                InlineKeyboardButton("📂 Categorias", callback_data="manage_categories"),
                InlineKeyboardButton("⚙️ Configurações", callback_data="settings")
            ],
            [
                InlineKeyboardButton("📋 Logs do Sistema", callback_data="system_logs"),
                InlineKeyboardButton("🔄 Sincronização", callback_data="sync_bots")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = (
            "🔧 *PAINEL ADMINISTRATIVO* 🔧\n\n"
            "Bem-vindo ao sistema de administração!\n"
            "Selecione uma opção abaixo:\n\n"
            "🛍️ *Gerenciar Serviços* - Adicionar/editar produtos\n"
            "👥 *Gerenciar Usuários* - Controle de usuários\n"
            "📊 *Relatórios* - Vendas e estatísticas\n"
            "💰 *Pagamentos* - Controle financeiro\n"
            "📂 *Categorias* - Organizar produtos\n"
            "⚙️ *Configurações* - Configurar sistema\n"
            "📋 *Logs* - Atividades do sistema\n"
            "🔄 *Sincronização* - Sync entre bots"
        )
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manipula callbacks dos botões inline"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        data = query.data
        
        if not self.is_admin(user_id):
            await query.edit_message_text("❌ Acesso negado!")
            return
        
        # Roteamento das callbacks
        if data == "main_menu":
            await self.show_main_menu(update, context)
        elif data == "manage_services":
            await self.manage_services_menu(update, context)
        elif data == "manage_users":
            await self.manage_users_menu(update, context)
        elif data == "reports":
            await self.show_reports(update, context)
        elif data == "payments":
            await self.payments_menu(update, context)
        elif data == "manage_categories":
            await self.manage_categories_menu(update, context)
        elif data == "settings":
            await self.settings_menu(update, context)
        elif data == "system_logs":
            await self.show_system_logs(update, context)
        elif data == "sync_bots":
            await self.sync_bots_menu(update, context)
        elif data.startswith("add_"):
            await self.handle_add_operations(update, context, data)
        elif data.startswith("edit_"):
            await self.handle_edit_operations(update, context, data)
        elif data.startswith("delete_"):
            await self.handle_delete_operations(update, context, data)
        elif data.startswith("view_"):
            await self.handle_view_operations(update, context, data)
    
    async def manage_services_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Menu de gerenciamento de serviços"""
        keyboard = [
            [
                InlineKeyboardButton("➕ Adicionar Serviço", callback_data="add_service"),
                InlineKeyboardButton("📝 Editar Serviço", callback_data="edit_service")
            ],
            [
                InlineKeyboardButton("📦 Gerenciar Estoque", callback_data="manage_stock"),
                InlineKeyboardButton("👁️ Ver Serviços", callback_data="view_services")
            ],
            [
                InlineKeyboardButton("🏷️ Adicionar Contas", callback_data="add_accounts"),
                InlineKeyboardButton("🗑️ Remover Serviço", callback_data="delete_service")
            ],
            [InlineKeyboardButton("🔙 Voltar", callback_data="main_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = (
            "🛍️ *GERENCIAR SERVIÇOS* 🛍️\n\n"
            "Escolha uma opção:\n\n"
            "➕ *Adicionar Serviço* - Criar novo produto\n"
            "📝 *Editar Serviço* - Modificar existente\n"
            "📦 *Gerenciar Estoque* - Controle de contas\n"
            "👁️ *Ver Serviços* - Listar produtos\n"
            "🏷️ *Adicionar Contas* - Inserir logins\n"
            "🗑️ *Remover Serviço* - Excluir produto"
        )
        
        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def manage_users_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Menu de gerenciamento de usuários"""
        keyboard = [
            [
                InlineKeyboardButton("👥 Ver Usuários", callback_data="view_users"),
                InlineKeyboardButton("🔍 Buscar Usuário", callback_data="search_user")
            ],
            [
                InlineKeyboardButton("💰 Ajustar Saldo", callback_data="adjust_balance"),
                InlineKeyboardButton("🚫 Bloquear/Desbloquear", callback_data="block_user")
            ],
            [
                InlineKeyboardButton("👑 Gerenciar Admins", callback_data="manage_admins"),
                InlineKeyboardButton("📊 Estatísticas", callback_data="user_stats")
            ],
            [InlineKeyboardButton("🔙 Voltar", callback_data="main_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = (
            "👥 *GERENCIAR USUÁRIOS* 👥\n\n"
            "Escolha uma opção:\n\n"
            "👥 *Ver Usuários* - Lista de usuários\n"
            "🔍 *Buscar Usuário* - Encontrar por ID/nome\n"
            "💰 *Ajustar Saldo* - Modificar saldo\n"
            "🚫 *Bloquear/Desbloquear* - Controle de acesso\n"
            "👑 *Gerenciar Admins* - Adicionar/remover admins\n"
            "📊 *Estatísticas* - Dados dos usuários"
        )
        
        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def show_reports(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Exibe relatórios e estatísticas"""
        # Buscar dados do banco
        total_users = len(db.execute_query("SELECT id FROM users") or [])
        total_services = len(db.execute_query("SELECT id FROM services WHERE is_active = TRUE") or [])
        total_transactions = db.execute_query("SELECT COUNT(*) as count FROM transactions WHERE status = 'completed'")[0][0]
        total_revenue = db.execute_query("SELECT SUM(amount) as total FROM transactions WHERE status = 'completed' AND type IN ('purchase', 'recharge')")[0][0] or 0
        
        # Transações recentes
        recent_transactions = db.execute_query("""
            SELECT t.*, u.first_name, s.name as service_name 
            FROM transactions t
            LEFT JOIN users u ON t.user_id = u.id
            LEFT JOIN services s ON t.service_id = s.id
            WHERE t.status = 'completed'
            ORDER BY t.created_at DESC
            LIMIT 5
        """) or []
        
        keyboard = [
            [
                InlineKeyboardButton("📈 Vendas por Período", callback_data="sales_period"),
                InlineKeyboardButton("🏆 Top Produtos", callback_data="top_products")
            ],
            [
                InlineKeyboardButton("💳 Relatório PIX", callback_data="pix_report"),
                InlineKeyboardButton("👤 Usuários Ativos", callback_data="active_users")
            ],
            [InlineKeyboardButton("🔙 Voltar", callback_data="main_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = (
            "📊 *RELATÓRIOS DO SISTEMA* 📊\n\n"
            f"👥 **Total de Usuários:** {total_users}\n"
            f"🛍️ **Serviços Ativos:** {total_services}\n"
            f"💳 **Total de Transações:** {total_transactions}\n"
            f"💰 **Receita Total:** R$ {total_revenue:.2f}\n\n"
            "🕒 **Últimas Transações:**\n"
        )
        
        for trans in recent_transactions[:3]:
            trans_type = "🛒 Compra" if trans[2] == 'purchase' else "💰 Recarga"
            text += f"• {trans_type}: R$ {trans[3]:.2f} - {trans[10] or 'Usuário'}\n"
        
        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def payments_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Menu de controle de pagamentos"""
        keyboard = [
            [
                InlineKeyboardButton("💳 Pagamentos Pendentes", callback_data="pending_payments"),
                InlineKeyboardButton("✅ Pagamentos Aprovados", callback_data="approved_payments")
            ],
            [
                InlineKeyboardButton("❌ Pagamentos Rejeitados", callback_data="rejected_payments"),
                InlineKeyboardButton("🔍 Buscar Pagamento", callback_data="search_payment")
            ],
            [
                InlineKeyboardButton("✅ Aprovar Manualmente", callback_data="manual_approve"),
                InlineKeyboardButton("❌ Rejeitar Pagamento", callback_data="manual_reject")
            ],
            [InlineKeyboardButton("🔙 Voltar", callback_data="main_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Estatísticas de pagamento
        pending = len(db.execute_query("SELECT id FROM pix_payments WHERE status = 'pending'") or [])
        approved = len(db.execute_query("SELECT id FROM pix_payments WHERE status = 'approved'") or [])
        
        text = (
            "💰 *CONTROLE DE PAGAMENTOS* 💰\n\n"
            f"⏳ **Pendentes:** {pending}\n"
            f"✅ **Aprovados:** {approved}\n\n"
            "Escolha uma opção para gerenciar os pagamentos:"
        )
        
        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def manage_categories_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Menu de gerenciamento de categorias"""
        categories = db.get_categories() or []
        
        keyboard = [
            [
                InlineKeyboardButton("➕ Adicionar Categoria", callback_data="add_category"),
                InlineKeyboardButton("📝 Editar Categoria", callback_data="edit_category")
            ],
            [
                InlineKeyboardButton("👁️ Ver Categorias", callback_data="view_categories"),
                InlineKeyboardButton("🗑️ Remover Categoria", callback_data="delete_category")
            ],
            [InlineKeyboardButton("🔙 Voltar", callback_data="main_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = (
            "📂 *GERENCIAR CATEGORIAS* 📂\n\n"
            f"📊 **Total de Categorias:** {len(categories)}\n\n"
            "Escolha uma opção:"
        )
        
        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manipula mensagens de texto"""
        user_id = update.effective_user.id
        text = update.message.text
        
        # Verificar se o usuário está em algum estado especial
        if user_id in self.user_states:
            state = self.user_states[user_id]
            
            if state == 'awaiting_password':
                if text == self.admin_password:
                    # Adicionar como admin
                    db.create_user(
                        user_id=user_id,
                        username=update.effective_user.username,
                        first_name=update.effective_user.first_name
                    )
                    db.add_admin(user_id, update.effective_user.username)
                    
                    del self.user_states[user_id]
                    await update.message.reply_text("✅ Acesso liberado! Bem-vindo, administrador!")
                    await self.show_main_menu(update, context)
                else:
                    await update.message.reply_text("❌ Senha incorreta!")
                return
            
            elif state.startswith('adding_service'):
                await self.handle_service_creation(update, context, state)
                return
            
            elif state.startswith('adding_category'):
                await self.handle_category_creation(update, context, state)
                return
            
            elif state.startswith('adding_account'):
                await self.handle_account_creation(update, context, state)
                return
    
    async def handle_add_operations(self, update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
        """Manipula operações de adição"""
        user_id = update.callback_query.from_user.id
        
        if data == "add_service":
            await update.callback_query.edit_message_text(
                "➕ *ADICIONAR SERVIÇO* ➕\n\n"
                "Por favor, envie o nome do serviço:",
                parse_mode='Markdown'
            )
            self.user_states[user_id] = 'adding_service_name'
        
        elif data == "add_category":
            await update.callback_query.edit_message_text(
                "➕ *ADICIONAR CATEGORIA* ➕\n\n"
                "Por favor, envie o nome da categoria:",
                parse_mode='Markdown'
            )
            self.user_states[user_id] = 'adding_category_name'
        
        elif data == "add_accounts":
            # Mostrar lista de serviços para adicionar contas
            services = db.get_services() or []
            if not services:
                await update.callback_query.edit_message_text(
                    "❌ Nenhum serviço encontrado!\n"
                    "Crie um serviço primeiro.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Voltar", callback_data="manage_services")
                    ]])
                )
                return
            
            keyboard = []
            for service in services[:10]:  # Limitar a 10 serviços
                keyboard.append([
                    InlineKeyboardButton(
                        f"{service[6]} {service[2]} (Estoque: {service[5]})",
                        callback_data=f"add_account_{service[0]}"
                    )
                ])
            keyboard.append([InlineKeyboardButton("🔙 Voltar", callback_data="manage_services")])
            
            await update.callback_query.edit_message_text(
                "🏷️ *ADICIONAR CONTAS* 🏷️\n\n"
                "Selecione o serviço para adicionar contas:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
        
        elif data.startswith("add_account_"):
            service_id = int(data.split("_")[2])
            service = db.get_service(service_id)
            
            await update.callback_query.edit_message_text(
                f"🏷️ *ADICIONAR CONTA - {service[2]}* 🏷️\n\n"
                "Envie os dados da conta no formato:\n"
                "`email:senha:informações_extras`\n\n"
                "Exemplo:\n"
                "`usuario@email.com:minhasenha:Plano Premium`",
                parse_mode='Markdown'
            )
            self.user_states[user_id] = f'adding_account_{service_id}'
    
    async def handle_service_creation(self, update: Update, context: ContextTypes.DEFAULT_TYPE, state: str):
        """Manipula a criação de serviços"""
        user_id = update.effective_user.id
        text = update.message.text
        
        if state == 'adding_service_name':
            # Armazenar nome do serviço temporariamente
            context.user_data['service_name'] = text
            
            # Buscar categorias
            categories = db.get_categories() or []
            if not categories:
                await update.message.reply_text(
                    "❌ Nenhuma categoria encontrada!\n"
                    "Crie uma categoria primeiro."
                )
                del self.user_states[user_id]
                return
            
            keyboard = []
            for cat in categories:
                keyboard.append([
                    InlineKeyboardButton(f"{cat[3]} {cat[1]}", callback_data=f"select_cat_{cat[0]}")
                ])
            
            await update.message.reply_text(
                "📂 Selecione a categoria:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            self.user_states[user_id] = 'adding_service_category'
        
        elif state == 'adding_service_price':
            try:
                price = float(text.replace(',', '.'))
                context.user_data['service_price'] = price
                
                await update.message.reply_text(
                    "📝 Envie a descrição do serviço:"
                )
                self.user_states[user_id] = 'adding_service_description'
            except ValueError:
                await update.message.reply_text(
                    "❌ Preço inválido! Envie um número válido:"
                )
        
        elif state == 'adding_service_description':
            description = text
            emoji = "🛍️"  # Emoji padrão
            
            # Criar serviço
            service_id = db.create_service(
                category_id=context.user_data['service_category'],
                name=context.user_data['service_name'],
                description=description,
                price=context.user_data['service_price'],
                emoji=emoji
            )
            
            if service_id:
                await update.message.reply_text(
                    f"✅ Serviço '{context.user_data['service_name']}' criado com sucesso!\n"
                    f"💰 Preço: R$ {context.user_data['service_price']:.2f}\n\n"
                    "Agora você pode adicionar contas para este serviço."
                )
                
                # Log da ação
                db.add_log(user_id, "service_created", f"Serviço: {context.user_data['service_name']}")
            else:
                await update.message.reply_text("❌ Erro ao criar serviço!")
            
            # Limpar estado
            del self.user_states[user_id]
            context.user_data.clear()
    
    async def handle_account_creation(self, update: Update, context: ContextTypes.DEFAULT_TYPE, state: str):
        """Manipula a criação de contas"""
        user_id = update.effective_user.id
        text = update.message.text
        
        service_id = int(state.split("_")[2])
        
        try:
            # Parsear dados da conta
            parts = text.split(":")
            if len(parts) < 2:
                await update.message.reply_text(
                    "❌ Formato inválido! Use:\n"
                    "`email:senha:informações_extras`"
                )
                return
            
            email = parts[0].strip()
            password = parts[1].strip()
            additional_info = parts[2].strip() if len(parts) > 2 else None
            
            # Adicionar conta
            account_id = db.add_account(service_id, email, password, additional_info)
            
            if account_id:
                service = db.get_service(service_id)
                await update.message.reply_text(
                    f"✅ Conta adicionada com sucesso!\n\n"
                    f"🛍️ **Serviço:** {service[2]}\n"
                    f"📧 **Email:** {email}\n"
                    f"📦 **Novo Estoque:** {service[5] + 1}"
                )
                
                # Log da ação
                db.add_log(user_id, "account_added", f"Serviço: {service[2]}, Email: {email}")
            else:
                await update.message.reply_text("❌ Erro ao adicionar conta!")
        
        except Exception as e:
            await update.message.reply_text(f"❌ Erro: {str(e)}")
        
        finally:
            del self.user_states[user_id]
    
    async def view_services(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Exibe lista de serviços"""
        services = db.get_services() or []
        
        if not services:
            await update.callback_query.edit_message_text(
                "❌ Nenhum serviço encontrado!",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Voltar", callback_data="manage_services")
                ]])
            )
            return
        
        text = "🛍️ *LISTA DE SERVIÇOS* 🛍️\n\n"
        
        for service in services[:10]:  # Limitar a 10 serviços
            status = "✅ Ativo" if service[7] else "❌ Inativo"
            text += (
                f"{service[6]} **{service[2]}**\n"
                f"💰 Preço: R$ {service[4]:.2f}\n"
                f"📦 Estoque: {service[5]}\n"
                f"📊 Status: {status}\n\n"
            )
        
        keyboard = [
            [InlineKeyboardButton("🔙 Voltar", callback_data="manage_services")]
        ]
        
        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    def run(self):
        """Executa o bot"""
        self.application = Application.builder().token(self.token).build()
        
        # Handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("adm", self.admin_command))
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Inicializar dados padrão
        self.init_default_data()
        
        print("🤖 Bot de Administração iniciado!")
        self.application.run_polling()
    
    def init_default_data(self):
        """Inicializa dados padrão no banco"""
        # Criar categoria padrão
        categories = db.get_categories()
        if not categories:
            db.create_category("Streaming", "Serviços de streaming de vídeo", "🎬")
            db.create_category("Jogos", "Contas de jogos e plataformas", "🎮")
            db.create_category("Música", "Serviços de streaming de música", "🎵")
            db.create_category("Software", "Licenças de software", "💻")
        
        # Adicionar admin principal
        if self.main_admin_id:
            db.create_user(self.main_admin_id, "MainAdmin", "Administrador Principal")
            db.add_admin(self.main_admin_id, "MainAdmin")

if __name__ == "__main__":
    bot = AdminBot()
    bot.run()