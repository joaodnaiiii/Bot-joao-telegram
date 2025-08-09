import os
from dotenv import load_dotenv

load_dotenv()

# Bot Tokens
ADMIN_BOT_TOKEN = "7405988960:AAEQWzK9-GMiRDSGGc_yLvAq3KMYvkL6DI0"
STORE_BOT_TOKEN = "8322262425:AAH3k6l9X6u1M4_FHNzG5HHLmELnfO6xqkM"

# Store Configuration
STORE_NAME = "JOAZINHO STORE"
STORE_IMAGE_URL = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRt5HttgP2EMD-PXpyyDGWRa75tIPm0vXvvXQnkCtYeWLarOUE7-Rr53jJ2&s=10"
SUPPORT_USERNAME = "@suporte_joaozinstore"
CLIENT_GROUP_LINK = "https://t.me/your_client_group"  # Replace with actual link

# Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'mysql+mysqlconnector://root:password@localhost/joazinho_store')

# Payment Configuration - PushinPay
PUSHINPAY_TOKEN = os.getenv('PUSHINPAY_TOKEN', 'your_pushinpay_token')
PIX_KEY = "62484d81-b9de-4b27-9fff-0c32f6e4c916"
MIN_RECHARGE = 2.00
MAX_RECHARGE = 1000.00
PIX_EXPIRY_MINUTES = 10

# Admin Configuration
ADMIN_IDS = [123456789]  # Replace with actual admin user IDs
ADMIN_DASHBOARD_EXPIRY = "26/11/2074"
SOFTWARE_VERSION = "V4.1.0"

# Bot Configuration
WEBHOOK_URL = os.getenv('WEBHOOK_URL', 'https://your-domain.com')
WEBHOOK_PORT = int(os.getenv('WEBHOOK_PORT', 5000))

# Encryption Key for sensitive data
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', 'joazinho-store-secret-key-2024!')

# Affiliate Settings
AFFILIATE_COMMISSION_RATE = 0.50  # 50% commission
AFFILIATE_STATUS = False  # Default disabled
POINTS_PER_RECHARGE = 10
MIN_POINTS_TO_CONVERT = 500
POINTS_MULTIPLIER = 0.01

# Registration Bonus
REGISTRATION_BONUS = 0.00

# Languages
SUPPORTED_LANGUAGES = ['pt', 'en']
DEFAULT_LANGUAGE = 'pt'

# Terms URL
TERMS_URL = "https://telegra.ph/TERMOS-DE-USO-E-POL%C3%8DTICA-DE-PRIVACIDADE-12-04"

# Log Destination
LOG_CHAT_ID = -1002531391775

# Separator for admin commands
ADMIN_SEPARATOR = "==="