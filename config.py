import os
from dotenv import load_dotenv

# Load variables from a .env file if present (useful for local development)
load_dotenv()

# Telegram bot tokens
ADMIN_BOT_TOKEN = os.getenv("ADMIN_BOT_TOKEN", "7405988960:AAEQWzK9-GMiRDSGGc_yLvAq3KMYvkL6DI0")
STORE_BOT_TOKEN = os.getenv("STORE_BOT_TOKEN", "8322262425:AAH3k6l9X6u1M4_FHNzG5HHLmELnfO6xqkM")

# List of Telegram user IDs that have admin privileges (comma-separated ints in env)
_ADMIN_IDS = os.getenv("ADMIN_IDS", "").split(",")
ADMIN_IDS = {int(x) for x in _ADMIN_IDS if x.isdigit()}

# Database configuration (defaulting to SQLite for ease of local testing)
DB_URL = os.getenv("DATABASE_URL", "sqlite:///database.db")