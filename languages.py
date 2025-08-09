TRANSLATIONS = {
    'pt': {
        # Main Menu
        'welcome': "🎉 Bem-vindo à JOAZINHO STORE! 🎉\n\n🚀 Sua loja de contas premium e serviços digitais!\n\nEscolha uma opção abaixo:",
        'main_menu': "📋 Menu Principal",
        'services_button': "🎮 Logins | Contas Premium",
        'profile_button': "👤 Perfil",
        'recharge_button': "💰 Recarga",
        'support_button': "🆘 Suporte",
        'search_button': "🔍 Pesquisar Serviço",
        'language_button': "🌐 Idioma",
        
        # Profile
        'profile_info': "👤 **SEU PERFIL**\n\n💰 Saldo: R$ {balance:.2f}\n🛒 Compras realizadas: {purchases}\n📅 Membro desde: {date}\n🔗 Código de indicação: `{referral_code}`\n\n💡 Indique amigos e ganhe 50% de comissão!",
        'purchase_history': "📊 Histórico de Compras",
        'referral_info': "🔗 Sistema de Indicação",
        
        # Services
        'services_list': "🎮 **SERVIÇOS DISPONÍVEIS**\n\nEscolha uma categoria:",
        'service_details': "🎯 **{name}**\n\n📝 {description}\n💰 Preço: R$ {price:.2f}\n📦 Estoque: {stock} disponível(is)\n\n✅ Entrega automática após pagamento!",
        'buy_service': "🛒 Comprar Agora",
        'insufficient_balance': "❌ Saldo insuficiente! Seu saldo: R$ {balance:.2f}\nValor necessário: R$ {price:.2f}\n\n💰 Faça uma recarga para continuar!",
        'purchase_success': "✅ **COMPRA REALIZADA COM SUCESSO!**\n\n🎯 Serviço: {service}\n💰 Valor: R$ {price:.2f}\n\n📧 **SEUS DADOS DE ACESSO:**\n👤 Login: `{login}`\n🔑 Senha: `{password}`\n{additional_info}\n\n⚠️ Guarde essas informações com segurança!",
        'out_of_stock': "❌ Produto fora de estoque! Tente novamente mais tarde.",
        
        # Recharge
        'recharge_menu': "💰 **RECARGA DE SALDO**\n\nDigite o valor que deseja recarregar (mínimo R$ 5,00):",
        'recharge_amount_invalid': "❌ Valor inválido! Digite um valor maior que R$ 5,00",
        'generating_pix': "⏳ Gerando QR Code PIX...",
        'pix_payment': "💳 **PAGAMENTO PIX**\n\n💰 Valor: R$ {amount:.2f}\n\n📱 Escaneie o QR Code abaixo ou use a chave PIX:\n\n🔑 Chave PIX: `{pix_key}`\n\n⏰ Este QR Code expira em 30 minutos.\n\n✅ O saldo será creditado automaticamente após confirmação do pagamento!",
        'payment_confirmed': "✅ **PAGAMENTO CONFIRMADO!**\n\n💰 Valor creditado: R$ {amount:.2f}\n💳 Novo saldo: R$ {balance:.2f}\n\n🎉 Obrigado pela recarga!",
        
        # Support
        'support_info': "🆘 **SUPORTE TÉCNICO**\n\n📞 Entre em contato conosco:\n\n💬 Telegram: @suporte_joazinho\n📧 Email: suporte@joazinhostore.com\n⏰ Horário: 24/7\n\n🚀 Resposta rápida garantida!",
        
        # Search
        'search_prompt': "🔍 Digite o nome do serviço que você procura:",
        'search_results': "🔍 **RESULTADOS DA BUSCA**\n\nEncontrados {count} resultado(s) para '{query}':",
        'no_results': "❌ Nenhum resultado encontrado para '{query}'",
        
        # Admin
        'admin_welcome': "👨‍💼 **PAINEL ADMINISTRATIVO**\n\nBem-vindo, administrador!\n\nEscolha uma opção:",
        'manage_services': "🎮 Gerenciar Serviços",
        'manage_users': "👥 Gerenciar Usuários",
        'sales_report': "📊 Relatório de Vendas",
        'system_config': "⚙️ Configurações",
        'broadcast': "📢 Enviar Mensagem",
        
        # Errors
        'error_generic': "❌ Ocorreu um erro. Tente novamente mais tarde.",
        'unauthorized': "❌ Você não tem permissão para acessar esta função.",
        'invalid_input': "❌ Entrada inválida. Tente novamente.",
        
        # Buttons
        'back': "⬅️ Voltar",
        'cancel': "❌ Cancelar",
        'confirm': "✅ Confirmar",
        'continue': "➡️ Continuar",
    },
    
    'en': {
        # Main Menu
        'welcome': "🎉 Welcome to JOAZINHO STORE! 🎉\n\n🚀 Your premium accounts and digital services store!\n\nChoose an option below:",
        'main_menu': "📋 Main Menu",
        'services_button': "🎮 Logins | Premium Accounts",
        'profile_button': "👤 Profile",
        'recharge_button': "💰 Recharge",
        'support_button': "🆘 Support",
        'search_button': "🔍 Search Service",
        'language_button': "🌐 Language",
        
        # Profile
        'profile_info': "👤 **YOUR PROFILE**\n\n💰 Balance: $ {balance:.2f}\n🛒 Purchases made: {purchases}\n📅 Member since: {date}\n🔗 Referral code: `{referral_code}`\n\n💡 Refer friends and earn 50% commission!",
        'purchase_history': "📊 Purchase History",
        'referral_info': "🔗 Referral System",
        
        # Services
        'services_list': "🎮 **AVAILABLE SERVICES**\n\nChoose a category:",
        'service_details': "🎯 **{name}**\n\n📝 {description}\n💰 Price: $ {price:.2f}\n📦 Stock: {stock} available\n\n✅ Automatic delivery after payment!",
        'buy_service': "🛒 Buy Now",
        'insufficient_balance': "❌ Insufficient balance! Your balance: $ {balance:.2f}\nRequired amount: $ {price:.2f}\n\n💰 Make a recharge to continue!",
        'purchase_success': "✅ **PURCHASE COMPLETED SUCCESSFULLY!**\n\n🎯 Service: {service}\n💰 Amount: $ {price:.2f}\n\n📧 **YOUR ACCESS DATA:**\n👤 Login: `{login}`\n🔑 Password: `{password}`\n{additional_info}\n\n⚠️ Keep this information secure!",
        'out_of_stock': "❌ Product out of stock! Try again later.",
        
        # Recharge
        'recharge_menu': "💰 **BALANCE RECHARGE**\n\nEnter the amount you want to recharge (minimum $ 5.00):",
        'recharge_amount_invalid': "❌ Invalid amount! Enter an amount greater than $ 5.00",
        'generating_pix': "⏳ Generating PIX QR Code...",
        'pix_payment': "💳 **PIX PAYMENT**\n\n💰 Amount: $ {amount:.2f}\n\n📱 Scan the QR Code below or use the PIX key:\n\n🔑 PIX Key: `{pix_key}`\n\n⏰ This QR Code expires in 30 minutes.\n\n✅ Balance will be credited automatically after payment confirmation!",
        'payment_confirmed': "✅ **PAYMENT CONFIRMED!**\n\n💰 Amount credited: $ {amount:.2f}\n💳 New balance: $ {balance:.2f}\n\n🎉 Thank you for the recharge!",
        
        # Support
        'support_info': "🆘 **TECHNICAL SUPPORT**\n\n📞 Contact us:\n\n💬 Telegram: @suporte_joazinho\n📧 Email: support@joazinhostore.com\n⏰ Hours: 24/7\n\n🚀 Quick response guaranteed!",
        
        # Search
        'search_prompt': "🔍 Type the name of the service you're looking for:",
        'search_results': "🔍 **SEARCH RESULTS**\n\nFound {count} result(s) for '{query}':",
        'no_results': "❌ No results found for '{query}'",
        
        # Admin
        'admin_welcome': "👨‍💼 **ADMIN PANEL**\n\nWelcome, administrator!\n\nChoose an option:",
        'manage_services': "🎮 Manage Services",
        'manage_users': "👥 Manage Users",
        'sales_report': "📊 Sales Report",
        'system_config': "⚙️ Settings",
        'broadcast': "📢 Send Message",
        
        # Errors
        'error_generic': "❌ An error occurred. Please try again later.",
        'unauthorized': "❌ You don't have permission to access this function.",
        'invalid_input': "❌ Invalid input. Please try again.",
        
        # Buttons
        'back': "⬅️ Back",
        'cancel': "❌ Cancel",
        'confirm': "✅ Confirm",
        'continue': "➡️ Continue",
    }
}

def get_text(key, lang='pt', **kwargs):
    """Get translated text with formatting"""
    text = TRANSLATIONS.get(lang, TRANSLATIONS['pt']).get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except KeyError:
            return text
    return text

def get_user_language(user_id, db):
    """Get user's preferred language from database"""
    from database import User
    user = db.query(User).filter(User.telegram_id == user_id).first()
    return user.language if user else 'pt'