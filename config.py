import os
from dotenv import load_dotenv

load_dotenv()

# Tokens dos Bots
ADMIN_BOT_TOKEN = "7405988960:AAEQWzK9-GMiRDSGGc_yLvAq3KMYvkL6DI0"
SHOP_BOT_TOKEN = "8322262425:AAH3k6l9X6u1M4_FHNzG5HHLmELnfO6xqkM"

# Configurações do Banco de Dados
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'password',
    'database': 'vendas_bot',
    'charset': 'utf8mb4'
}

# Configurações de Pagamento (Mercado Pago)
MERCADO_PAGO_ACCESS_TOKEN = os.getenv('MERCADO_PAGO_ACCESS_TOKEN', '')
MERCADO_PAGO_PUBLIC_KEY = os.getenv('MERCADO_PAGO_PUBLIC_KEY', '')

# Configurações do Sistema
ADMIN_IDS = [123456789]  # IDs dos administradores
COMMISSION_RATE = 0.5  # 50% de comissão para afiliados
MIN_RECHARGE_AMOUNT = 10.0  # Valor mínimo de recarga
MAX_RECHARGE_AMOUNT = 1000.0  # Valor máximo de recarga

# Configurações de Segurança
ENCRYPTION_KEY = b'your-32-byte-encryption-key-here-!!!!'

# Mensagens do Sistema
MESSAGES = {
    'welcome': '🎯 **Bem-vindo ao Bot de Vendas!**\n\nEscolha uma opção abaixo:',
    'admin_welcome': '🔧 **Painel Administrativo**\n\nSelecione uma opção:',
    'payment_success': '✅ **Pagamento Confirmado!**\n\nSeu pedido foi processado com sucesso.',
    'insufficient_balance': '❌ **Saldo Insuficiente**\n\nRecarregue sua conta para continuar.',
    'service_unavailable': '⚠️ **Serviço Indisponível**\n\nEste serviço está temporariamente fora de estoque.'
}

# Configurações de Idiomas
LANGUAGES = {
    'pt': 'Português',
    'en': 'English'
}

# Emojis para Categorias
CATEGORY_EMOJIS = {
    'streaming': '📺',
    'games': '🎮',
    'music': '🎵',
    'vpn': '🔒',
    'education': '📚',
    'software': '💻',
    'other': '🔧'
}