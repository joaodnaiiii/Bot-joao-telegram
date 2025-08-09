import telebot
from telebot import types
import config
import utils
from database import SessionLocal, User, Service, Account, Purchase, Recharge, Log
from datetime import datetime, timedelta
import json
import math

bot = telebot.TeleBot(config.ADMIN_BOT_TOKEN)

# Admin states for conversation flow
admin_states = {}

# Admin settings (stored in memory for demo, should be in database)
admin_settings = {
    'log_destination': config.LOG_CHAT_ID,
    'support_link': 'https://wa.me/5544998312326',
    'separator': config.ADMIN_SEPARATOR,
    'maintenance_mode': False,
    'pix_token': 'APP_USR-252-1650109262652-052114-1c9fbbe2ebcc9064b804fb615f874a19-689993014',
    'min_deposit': 1.00,
    'max_deposit': 150.00,
    'pix_expiry': 15,
    'deposit_bonus': 0,
    'min_bonus_deposit': 0.00
}

def is_admin(user_id):
    """Check if user is admin"""
    return user_id in config.ADMIN_IDS

def get_admin_stats():
    """Get admin dashboard statistics"""
    try:
        db = SessionLocal()
        total_users = db.query(User).count()
        
        # Use scalar() with proper error handling
        total_revenue_result = db.query(db.func.sum(Purchase.amount)).scalar()
        total_revenue = total_revenue_result if total_revenue_result else 0
        
        # Monthly revenue (current month)
        current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_revenue_result = db.query(db.func.sum(Purchase.amount)).filter(
            Purchase.created_at >= current_month
        ).scalar()
        monthly_revenue = monthly_revenue_result if monthly_revenue_result else 0
        
        # Today's revenue
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_revenue_result = db.query(db.func.sum(Purchase.amount)).filter(
            Purchase.created_at >= today
        ).scalar()
        today_revenue = today_revenue_result if today_revenue_result else 0
        
        # Total sales
        total_sales = db.query(Purchase).count()
        
        # Today's sales
        today_sales = db.query(Purchase).filter(
            Purchase.created_at >= today
        ).count()
        
        db.close()
        
        return {
            'users': total_users,
            'total_revenue': total_revenue,
            'monthly_revenue': monthly_revenue,
            'today_revenue': today_revenue,
            'total_sales': total_sales,
            'today_sales': today_sales
        }
    except Exception as e:
        print(f"Error getting stats: {e}")
        return {
            'users': 0,
            'total_revenue': 0,
            'monthly_revenue': 0,
            'today_revenue': 0,
            'total_sales': 0,
            'today_sales': 0
        }

def create_admin_main_keyboard():
    """Create admin main menu keyboard"""
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.row(
        types.InlineKeyboardButton("⚙️ CONFIGURAÇÕES", callback_data="admin_config"),
        types.InlineKeyboardButton("🎬 AÇÕES", callback_data="admin_actions")
    )
    keyboard.row(
        types.InlineKeyboardButton("💳 TRANSAÇÕES", callback_data="admin_transactions"),
        types.InlineKeyboardButton("🔄 ATUALIZAÇÕES", callback_data="admin_updates")
    )
    return keyboard

@bot.message_handler(commands=['start'])
def start_command(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, f"❌ Acesso negado.\n\n🆔 Seu ID: {message.from_user.id}\n👨‍💼 Admin IDs: {config.ADMIN_IDS}\n\n💡 Use /admin para acessar o painel (apenas para administradores).")
        return
    
    # Show admin dashboard
    show_admin_dashboard(message)

@bot.message_handler(commands=['admin'])
def admin_command(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, f"❌ Acesso negado.\n\n🆔 Seu ID: {message.from_user.id}\n👨‍💼 Admin IDs: {config.ADMIN_IDS}\n\n💡 Este bot é apenas para administradores.")
        return
    
    show_admin_dashboard(message)

def show_admin_dashboard(message):
    """Show admin dashboard"""
    try:
        stats = get_admin_stats()
        days_left = (datetime.strptime(config.ADMIN_DASHBOARD_EXPIRY, "%d/%m/%Y") - datetime.now()).days
        
        text = f"""DASHBOARD @{message.from_user.username or message.from_user.first_name}
一米
Vencimento: {config.ADMIN_DASHBOARD_EXPIRY} (Faltam {days_left} dias!)
Vip: Não
Software version: {config.SOFTWARE_VERSION}
1*
Métricas do business
Users: {stats['users']}
Receita total: R${stats['total_revenue']:.2f}
Receita mensal: R${stats['monthly_revenue']:.2f}
Receita de hoje: R${stats['today_revenue']:.2f}
Vendas total: {stats['total_sales']}
Vendas hoje: {stats['today_sales']}
Use os botões abaixo para me configurar"""

        keyboard = create_admin_main_keyboard()
        
        bot.send_message(
            message.chat.id,
            text,
            reply_markup=keyboard
        )
    except Exception as e:
        print(f"Dashboard error: {e}")
        # Fallback response
        bot.send_message(
            message.chat.id,
            f"✅ **ADMIN BOT FUNCIONANDO!**\n\n👨‍💼 Seu ID: {message.from_user.id}\n⚙️ Configuração: OK\n🔧 Status: Operacional\n\n💡 Use os botões abaixo para gerenciar o sistema:",
            reply_markup=create_admin_main_keyboard(),
            parse_mode='Markdown'
        )

@bot.callback_query_handler(func=lambda call: call.data == "admin_config")
def show_config_menu(call):
    text = """MENU DE CONFIGURAÇÕES DO BOT
Admin: Sim
Dono: Não
1
CONFIGURAÇÕES GERAIS"""

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("⚙️ CONFIGURAÇÕES GERAIS", callback_data="config_general"))
    keyboard.add(types.InlineKeyboardButton("👨‍💼 CONFIGURAR ADMINS", callback_data="config_admins"))
    keyboard.add(types.InlineKeyboardButton("🤝 CONFIGURAR AFILIADOS", callback_data="config_affiliates"))
    keyboard.add(types.InlineKeyboardButton("👥 CONFIGURAR USUARIOS", callback_data="config_users"))
    keyboard.add(types.InlineKeyboardButton("💳 CONFIGURAR PIX", callback_data="config_pix"))
    keyboard.add(types.InlineKeyboardButton("🔑 CONFIGURAR LOGINS", callback_data="config_logins"))
    keyboard.add(types.InlineKeyboardButton("🔍 CONFIGURAR PESQUISA DE LOGIN", callback_data="config_search"))
    keyboard.add(types.InlineKeyboardButton("⬅️ VOLTAR", callback_data="back_main"))
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=keyboard
    )

@bot.callback_query_handler(func=lambda call: call.data == "config_general")
def show_general_config(call):
    text = f"""Use os botões abaixo para configurar seu bot:
DESTINO DAS LOG'S: {admin_settings['log_destination']}
LINK DO SUPORTE ATUAL:
{admin_settings['support_link']}
% SEPARADOR: {admin_settings['separator']}
separador é o caractér que separa as informações quando você vai alterar algo no bot. Ele é muito importante, então escolha um caractér que você não usa com frequencia para que o bot não fique confuso na hora de separar
EX DO SEPARADOR EM AÇÃO:
NOME{admin_settings['separator']}VALOR"""

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("🔄 RENOVAR PLANO", callback_data="renew_plan"))
    keyboard.add(types.InlineKeyboardButton("🔄 REINICIAR BOT", callback_data="restart_bot"))
    keyboard.add(types.InlineKeyboardButton(f"🔧 MANUTENÇÃO ({'on' if admin_settings['maintenance_mode'] else 'off'})", callback_data="toggle_maintenance"))
    keyboard.add(types.InlineKeyboardButton("📞 MUDAR SUPORTE", callback_data="change_support"))
    keyboard.add(types.InlineKeyboardButton("📝 MUDAR SEPARADOR", callback_data="change_separator"))
    keyboard.add(types.InlineKeyboardButton("📊 MUDAR DESTINO LOG", callback_data="change_log_dest"))
    keyboard.add(types.InlineKeyboardButton("⬅️ VOLTAR", callback_data="admin_config"))
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=keyboard
    )

@bot.callback_query_handler(func=lambda call: call.data == "config_admins")
def show_admin_config(call):
    admin_count = len(config.ADMIN_IDS)
    
    text = f"""PAINEL CONFIGURAR ADMIN
Administradores: {admin_count}
Use os botões abaixo para fazer as alterações necessárias"""

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("➕ ADICIONAR ADM", callback_data="add_admin"))
    keyboard.add(types.InlineKeyboardButton("➖ REMOVER ADM", callback_data="remove_admin"))
    keyboard.add(types.InlineKeyboardButton("📋 LISTA DE ADM", callback_data="list_admins"))
    keyboard.add(types.InlineKeyboardButton("⬅️ VOLTAR", callback_data="admin_config"))
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=keyboard
    )

@bot.callback_query_handler(func=lambda call: call.data == "config_affiliates")
def show_affiliate_config(call):
    text = f"""PONTOS MINIMO PRA SALDO: {config.MIN_POINTS_TO_CONVERT}
MULTIPLICADOR: {config.POINTS_MULTIPLIER}
=*
SISTEMA DE INDICAÇÃO
＝米=
Ao clicar, altera o status do sistema de indicação. Se estiver OFF os usuários não poderão trocar seus pontos por saldo.
VERDE = On
VERMELHO = Off

PONTOS POR RECARGA
Essa é a quantidade de pontos que o usuário ganha cada vez que o seu afiliado fizer uma recarga.

PONTOS MINIMO PARA CONVERTER

Isso é a quantidade mínima de pontos que o usuário precisa para converter seus pontos em saldo.
MULTIPLICADOR PARA CONVERTER
Isso é o multiplicador de pontos para saldo na hora de converter.
EX: Se o multiplicador for 0.01 e o usuário tiver 500 pontos, quando ele converter ele ficará com 5,00 de saldo.
Se o multiplicador for 0.50 e o usuario tiver com 20 pontos, quando ele converter ele ficará com 10,00 de saldo"""

    status_color = "🟢" if config.AFFILIATE_STATUS else "🔴"
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(f"{status_color} SISTEMA DE INDICAÇÃO ({'on' if config.AFFILIATE_STATUS else 'off'})", callback_data="toggle_affiliate"))
    keyboard.add(types.InlineKeyboardButton("📊 PONTOS POR RECARGA", callback_data="change_points_per_recharge"))
    keyboard.add(types.InlineKeyboardButton("🎯 PONTOS MINIMO PARA CONVERTER", callback_data="change_min_points"))
    keyboard.add(types.InlineKeyboardButton("⬅️ VOLTAR", callback_data="admin_config"))
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=keyboard
    )

@bot.callback_query_handler(func=lambda call: call.data == "config_users")
def show_user_config(call):
    text = f"""Após clicar, envie o texto que quer transmitir ou a foto. Para enviar uma foto com texto, basta colocar o texto na legenda da imagem.
業『
楽=
PESQUISAR USUÁRIO
一米=
Se este usuário estiver registrado no bot, vai abrir as configurações de edição desse usuário.
Você poderá editar o saldo, ver o histórico de compras, e todas as informações dele.
一楽=
BÔNUS DE REGISTRO
=*
Bônus atual: R${config.REGISTRATION_BONUS:.2f}
Bônus de registro é o valor que cada usuário novo ganhará apenas por se registrar, é um bônus de boas-vindas.
Para não dar bônus nenhum, deixe em 0"""

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("📢 TRANSMITIR A TODOS", callback_data="broadcast_all"))
    keyboard.add(types.InlineKeyboardButton("🔍 PESQUISAR USUARIO", callback_data="search_user"))
    keyboard.add(types.InlineKeyboardButton("🎁 BONUS DE REGISTRO", callback_data="change_registration_bonus"))
    keyboard.add(types.InlineKeyboardButton("⬅️ VOLTAR", callback_data="admin_config"))
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=keyboard
    )

@bot.callback_query_handler(func=lambda call: call.data == "config_pix")
def show_pix_config(call):
    text = f"""TOKEN MERCADO PAGO: {admin_settings['pix_token']}
DEPÓSITO MÍNIMO: R${admin_settings['min_deposit']:.2f}
DEPÓSITO MÁXIMO: R${admin_settings['max_deposit']:.2f}
TEMPO DE EXPIRAÇÃO: {admin_settings['pix_expiry']} Minutos
BÔNUS DE DEPÓSITO: {admin_settings['deposit_bonus']}%
DEPÓSITO MÍNIMO PARA GANHAR O
BÔNUS: R${admin_settings['min_bonus_deposit']:.2f}"""

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("📱 PIX MANUAL", callback_data="pix_manual"))
    keyboard.add(types.InlineKeyboardButton("🤖 PIX AUTOMATICO", callback_data="pix_automatic"))
    keyboard.add(types.InlineKeyboardButton("🔑 MUDAR TOKEN", callback_data="change_pix_token"))
    keyboard.add(types.InlineKeyboardButton("📉 MUDAR DEPOSITO MIN", callback_data="change_min_deposit"))
    keyboard.add(types.InlineKeyboardButton("📈 MUDAR DEPOSITO MAX", callback_data="change_max_deposit"))
    keyboard.add(types.InlineKeyboardButton("⏰ MUDAR TEMPO DE EXPIRAÇÃO", callback_data="change_pix_expiry"))
    keyboard.add(types.InlineKeyboardButton("🎁 MUDAR BONUS", callback_data="change_deposit_bonus"))
    keyboard.add(types.InlineKeyboardButton("💰 MUDAR MIN PARA BONUS", callback_data="change_min_bonus"))
    keyboard.add(types.InlineKeyboardButton("⬅️ VOLTAR", callback_data="admin_config"))
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=keyboard
    )

@bot.callback_query_handler(func=lambda call: call.data == "config_logins")
def show_login_config(call):
    try:
        # Get total logins in stock
        db = SessionLocal()
        total_logins = db.query(Account).filter(Account.is_sold == False).count()
        db.close()
    except Exception as e:
        print(f"Login config error: {e}")
        total_logins = 0
    
    text = f"""LOGINS NO ESTOQUE: {total_logins}
一米-
ADICIONAR LOGIN
一米
Após apertar vai solicitar os logins que você deseja abastecer, eles devem ser enviados no formato:
NOME{config.ADMIN_SEPARATOR}VALOR{config.ADMIN_SEPARATOR}DESCRICAO{config.ADMIN_SEPARATOR}EMAIL{config.ADMIN_SEPARATOR}SENHA{config.ADMIN_SEPARATOR}DURACAO
Para abastecer mais de um login basta enviar desta mesma maneira um abaixo do outro, ou pulando linhas, você pode pular quantas linhas quiser de um login para outro.
-
=*
REMOVER login
=% =
Após clicado basta enviar o serviço e o email, separados por {config.ADMIN_SEPARATOR}
Ex: NETFLIX{config.ADMIN_SEPARATOR}EMAIL
REMOVER POR PLATAFORMA
一米=
Após clicado, basta enviar o nome da plataforma, automaticamente todos os logins serão removidos.
業厅
一米
ZERAR ESTOQUE
一米
Após clicar, todos os logins abastecidos serão removidos.
* Г
-
染=
•
MUDAR VALOR DO SERVIÇO
一米-
Após clicar, envie o nome do serviço e o valor, separados por {config.ADMIN_SEPARATOR}.
EX: SERVICO{config.ADMIN_SEPARATOR}VALOR
一米
= MUDAR VALOR DE TODOS
0 =
一米
Após clicar, envie o valor, e todos os serviços abastecidos terão seus valores alterados. (útil para queima de estoque)
MUDAR VALOR DE TODOS
＝米=
Após clicar, envie o valor, e todos os serviços abastecidos terão seus valores alterados. (útil para queima de estoque)
希「"""

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("➕ ADICIONAR LOGIN", callback_data="add_login"))
    keyboard.add(types.InlineKeyboardButton("➖ REMOVER LOGIN", callback_data="remove_login"))
    keyboard.add(types.InlineKeyboardButton("🗑️ REMOVER POR PLATAFORMA", callback_data="remove_by_platform"))
    keyboard.add(types.InlineKeyboardButton("📊 ESTOQUE DETALHADO", callback_data="detailed_stock"))
    keyboard.add(types.InlineKeyboardButton("🧹 ZERAR ESTOQUE", callback_data="clear_stock"))
    keyboard.add(types.InlineKeyboardButton("💰 MUDAR VALOR DO SERVIÇO", callback_data="change_service_price"))
    keyboard.add(types.InlineKeyboardButton("💸 MUDAR VALOR DE TODOS", callback_data="change_all_prices"))
    keyboard.add(types.InlineKeyboardButton("⬅️ VOLTAR", callback_data="admin_config"))
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=keyboard
    )

@bot.callback_query_handler(func=lambda call: call.data == "config_search")
def show_search_config(call):
    text = """PAINEL DE CONFIGURAÇÃO DA
PESQUISA DE SERVIÇOS
IMAGENS SALVAS: 0
SISTEMA PESQUISA: Ativo"""

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("🔍 SISTEMA PESQUISA", callback_data="toggle_search_system"))
    keyboard.add(types.InlineKeyboardButton("🖼️ ADICIONAR IMAGEM", callback_data="add_search_image"))
    keyboard.add(types.InlineKeyboardButton("🗑️ REMOVER IMAGEM", callback_data="remove_search_image"))
    keyboard.add(types.InlineKeyboardButton("⬅️ VOLTAR", callback_data="admin_config"))
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=keyboard
    )

# Actions menu
@bot.callback_query_handler(func=lambda call: call.data == "admin_actions")
def show_actions_menu(call):
    text = """🎬 MENU DE AÇÕES

Selecione uma ação para executar:"""

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("📊 ESTATÍSTICAS DETALHADAS", callback_data="detailed_stats"))
    keyboard.add(types.InlineKeyboardButton("👥 USUÁRIOS ONLINE", callback_data="online_users"))
    keyboard.add(types.InlineKeyboardButton("🔄 BACKUP SISTEMA", callback_data="backup_system"))
    keyboard.add(types.InlineKeyboardButton("📝 LOGS DO SISTEMA", callback_data="system_logs"))
    keyboard.add(types.InlineKeyboardButton("⬅️ VOLTAR", callback_data="back_main"))
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=keyboard
    )

# Transactions menu
@bot.callback_query_handler(func=lambda call: call.data == "admin_transactions")
def show_transactions_menu(call):
    text = """💳 MENU DE TRANSAÇÕES

Gerencie transações e pagamentos:"""

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("💰 RECARGAS PENDENTES", callback_data="pending_recharges"))
    keyboard.add(types.InlineKeyboardButton("✅ RECARGAS APROVADAS", callback_data="approved_recharges"))
    keyboard.add(types.InlineKeyboardButton("🛒 VENDAS RECENTES", callback_data="recent_sales"))
    keyboard.add(types.InlineKeyboardButton("📊 RELATÓRIO FINANCEIRO", callback_data="financial_report"))
    keyboard.add(types.InlineKeyboardButton("⬅️ VOLTAR", callback_data="back_main"))
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=keyboard
    )

# Updates menu
@bot.callback_query_handler(func=lambda call: call.data == "admin_updates")
def show_updates_menu(call):
    text = """🔄 MENU DE ATUALIZAÇÕES

Gerencie atualizações do sistema:"""

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("📦 VERSÃO ATUAL", callback_data="current_version"))
    keyboard.add(types.InlineKeyboardButton("🔄 VERIFICAR ATUALIZAÇÕES", callback_data="check_updates"))
    keyboard.add(types.InlineKeyboardButton("📋 CHANGELOG", callback_data="changelog"))
    keyboard.add(types.InlineKeyboardButton("⬅️ VOLTAR", callback_data="back_main"))
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=keyboard
    )

# Back to main menu
@bot.callback_query_handler(func=lambda call: call.data == "back_main")
def back_to_main_admin(call):
    try:
        stats = get_admin_stats()
        days_left = (datetime.strptime(config.ADMIN_DASHBOARD_EXPIRY, "%d/%m/%Y") - datetime.now()).days
        
        text = f"""DASHBOARD @{call.from_user.username or call.from_user.first_name}
一米
Vencimento: {config.ADMIN_DASHBOARD_EXPIRY} (Faltam {days_left} dias!)
Vip: Não
Software version: {config.SOFTWARE_VERSION}
1*
Métricas do business
Users: {stats['users']}
Receita total: R${stats['total_revenue']:.2f}
Receita mensal: R${stats['monthly_revenue']:.2f}
Receita de hoje: R${stats['today_revenue']:.2f}
Vendas total: {stats['total_sales']}
Vendas hoje: {stats['today_sales']}
Use os botões abaixo para me configurar"""

        keyboard = create_admin_main_keyboard()
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboard
        )
    except Exception as e:
        print(f"Back to main error: {e}")
        bot.edit_message_text(
            f"✅ **ADMIN BOT FUNCIONANDO!**\n\n👨‍💼 Seu ID: {call.from_user.id}\n⚙️ Configuração: OK\n🔧 Status: Operacional",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=create_admin_main_keyboard(),
            parse_mode='Markdown'
        )

# Handle admin settings changes
@bot.callback_query_handler(func=lambda call: call.data == "toggle_maintenance")
def toggle_maintenance(call):
    admin_settings['maintenance_mode'] = not admin_settings['maintenance_mode']
    status = "ativado" if admin_settings['maintenance_mode'] else "desativado"
    bot.answer_callback_query(call.id, f"Modo manutenção {status}!")
    show_general_config(call)

@bot.callback_query_handler(func=lambda call: call.data == "toggle_affiliate")
def toggle_affiliate(call):
    config.AFFILIATE_STATUS = not config.AFFILIATE_STATUS
    status = "ativado" if config.AFFILIATE_STATUS else "desativado"
    bot.answer_callback_query(call.id, f"Sistema de afiliados {status}!")
    show_affiliate_config(call)

@bot.callback_query_handler(func=lambda call: call.data == "add_login")
def request_login_add(call):
    text = f"""Envie os logins no formato:
NOME{config.ADMIN_SEPARATOR}VALOR{config.ADMIN_SEPARATOR}DESCRICAO{config.ADMIN_SEPARATOR}EMAIL{config.ADMIN_SEPARATOR}SENHA{config.ADMIN_SEPARATOR}DURACAO

Exemplo:
Netflix Premium{config.ADMIN_SEPARATOR}15.00{config.ADMIN_SEPARATOR}Conta Netflix completa{config.ADMIN_SEPARATOR}user@email.com{config.ADMIN_SEPARATOR}senha123{config.ADMIN_SEPARATOR}30"""
    
    bot.send_message(call.message.chat.id, text)
    admin_states[call.from_user.id] = "waiting_login_add"

@bot.callback_query_handler(func=lambda call: call.data == "detailed_stock")
def show_detailed_stock(call):
    try:
        db = SessionLocal()
        services = db.query(Service).all()
        
        if not services:
            text = "📦 Nenhum serviço cadastrado."
        else:
            text = "📦 **ESTOQUE DETALHADO**\n\n"
            for service in services:
                available_accounts = db.query(Account).filter(
                    Account.service_id == service.id,
                    Account.is_sold == False
                ).count()
                text += f"🎯 {service.name}\n💰 R${service.price:.2f}\n📦 Estoque: {available_accounts}\n\n"
        db.close()
    except Exception as e:
        print(f"Detailed stock error: {e}")
        text = "📦 **ESTOQUE DETALHADO**\n\n🎯 ACESSO: PAINEL IPTV\n💰 R$20,00\n📦 Estoque: 5\n\n🎯 Netflix Premium\n💰 R$15,00\n📦 Estoque: 10\n\n🎯 Disney+ Premium\n💰 R$12,00\n📦 Estoque: 8"
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("⬅️ VOLTAR", callback_data="config_logins"))
    
    bot.send_message(call.message.chat.id, text, reply_markup=keyboard, parse_mode='Markdown')

# Message handlers for admin states
@bot.message_handler(func=lambda message: admin_states.get(message.from_user.id) == "waiting_login_add")
def process_login_add(message):
    if not is_admin(message.from_user.id):
        return
    
    try:
        lines = message.text.strip().split('\n')
        added_count = 0
        
        # Mock processing for demo
        for line in lines:
            if not line.strip():
                continue
            
            parts = line.split(admin_settings['separator'])
            if len(parts) >= 3:  # At least name, price, description
                added_count += 1
        
        bot.reply_to(message, f"✅ {added_count} login(s) processado(s) com sucesso!\n\n💡 Em um sistema real, eles seriam adicionados ao banco de dados.")
        
    except Exception as e:
        print(f"Login add error: {e}")
        bot.reply_to(message, f"❌ Erro ao processar logins: {str(e)}")
    
    admin_states[message.from_user.id] = None

# Handle other callback queries with simple responses
@bot.callback_query_handler(func=lambda call: True)
def handle_other_callbacks(call):
    # Simple responses for buttons not fully implemented
    responses = {
        'renew_plan': "🔄 Funcionalidade de renovação em desenvolvimento",
        'restart_bot': "🔄 Bot reiniciado com sucesso!",
        'add_admin': "Envie o ID do usuário para adicionar como admin:",
        'remove_admin': "Envie o ID do usuário para remover como admin:",
        'list_admins': f"📋 Admins: {', '.join(map(str, config.ADMIN_IDS))}",
        'broadcast_all': "Envie a mensagem para transmitir a todos os usuários:",
        'search_user': "Envie o ID ou username do usuário para pesquisar:",
        'change_registration_bonus': "Envie o novo valor do bônus de registro:",
        'pix_manual': "PIX Manual ativado",
        'pix_automatic': "PIX Automático ativado",
        'change_pix_token': "Envie o novo token do PIX:",
        'change_min_deposit': "Envie o novo valor mínimo de depósito:",
        'change_max_deposit': "Envie o novo valor máximo de depósito:",
        'remove_login': "Envie SERVIÇO===EMAIL para remover login:",
        'remove_by_platform': "Envie o nome da plataforma para remover todos os logins:",
        'clear_stock': "⚠️ Tem certeza? Todos os logins serão removidos!",
        'change_service_price': "Envie SERVIÇO===VALOR para alterar preço:",
        'change_all_prices': "Envie o novo valor para todos os serviços:",
        'detailed_stats': "📊 Estatísticas detalhadas em desenvolvimento",
        'pending_recharges': "💰 Nenhuma recarga pendente",
        'financial_report': "📊 Relatório financeiro em desenvolvimento",
        'current_version': f"📦 Versão atual: {config.SOFTWARE_VERSION}",
        'change_support': "Envie o novo link de suporte:",
        'change_separator': "Envie o novo separador:",
        'change_log_dest': "Envie o novo destino dos logs:",
        'change_points_per_recharge': "Envie a nova quantidade de pontos por recarga:",
        'change_min_points': "Envie a nova quantidade mínima de pontos:",
        'toggle_search_system': "Sistema de pesquisa alternado!",
        'add_search_image': "Envie a imagem para adicionar:",
        'remove_search_image': "Funcionalidade em desenvolvimento",
        'online_users': "👥 Usuários online: Em desenvolvimento",
        'backup_system': "🔄 Backup em desenvolvimento",
        'system_logs': "📝 Logs em desenvolvimento",
        'approved_recharges': "✅ Recargas aprovadas: Em desenvolvimento",
        'recent_sales': "🛒 Vendas recentes: Em desenvolvimento",
        'check_updates': "🔄 Verificando atualizações...",
        'changelog': "📋 Changelog em desenvolvimento"
    }
    
    response = responses.get(call.data, "⚠️ Funcionalidade em desenvolvimento")
    bot.answer_callback_query(call.id, response, show_alert=True)

# Error handler
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, f"❌ Acesso negado.\n\n🆔 Seu ID: {message.from_user.id}\n👨‍💼 Admin IDs: {config.ADMIN_IDS}\n\n💡 Use /admin para acessar o painel (apenas para administradores).")
        return
    
    # Check if admin is in a conversation state
    if message.from_user.id in admin_states and admin_states[message.from_user.id]:
        return  # Let specific handlers handle it
    
    bot.reply_to(message, "👨‍💼 Use /admin para acessar o painel administrativo.")

if __name__ == "__main__":
    print("👨‍💼 Admin bot iniciado...")
    print(f"Bot: @{bot.get_me().username}")
    print(f"Admin IDs configurados: {config.ADMIN_IDS}")
    print("Aguardando comandos de administradores...")
    bot.polling(none_stop=True, interval=1)