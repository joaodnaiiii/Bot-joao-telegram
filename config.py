import os
from dotenv import load_dotenv

load_dotenv()

# Bot Tokens
ADMIN_BOT_TOKEN = "7405988960:AAEQWzK9-GMiRDSGGc_yLvAq3KMYvkL6DI0"
STORE_BOT_TOKEN = "8322262425:AAH3k6l9X6u1M4_FHNzG5HHLmELnfO6xqkM"

# Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'mysql+mysqlconnector://root:password@localhost/bot_store')

# Payment Configuration
MERCADOPAGO_ACCESS_TOKEN = os.getenv('MERCADOPAGO_ACCESS_TOKEN', '')
PIX_KEY = os.getenv('PIX_KEY', '62484d81-b9de-4b27-9fff-0c32f6e4c916')

# Admin Configuration
ADMIN_IDS = [123456789]  # Replace with actual admin user IDs

# Bot Configuration
WEBHOOK_URL = os.getenv('WEBHOOK_URL', 'https://your-domain.com')
WEBHOOK_PORT = int(os.getenv('WEBHOOK_PORT', 5000))

# Encryption Key for sensitive data
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', 'your-secret-key-here-32-chars!')

# Commission Settings
AFFILIATE_COMMISSION_RATE = 0.50  # 50% commission

# Languages
SUPPORTED_LANGUAGES = ['pt', 'en']
DEFAULT_LANGUAGE = 'pt'