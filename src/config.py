import os
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseModel):
    shop_bot_token: str = os.getenv("SHOP_BOT_TOKEN", "")
    admin_bot_token: str = os.getenv("ADMIN_BOT_TOKEN", "")
    admin_telegram_ids: list[int] = (
        [int(x.strip()) for x in os.getenv("ADMIN_TELEGRAM_IDS", "").split(",") if x.strip()]
    )

    database_url: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data.db")

    default_language: str = os.getenv("DEFAULT_LANGUAGE", "pt")
    currency: str = os.getenv("CURRENCY", "BRL")
    affiliate_commission_percent: int = int(os.getenv("AFFILIATE_COMMISSION_PERCENT", "50"))

    payment_provider: str = os.getenv("PAYMENT_PROVIDER", "mock")
    mp_access_token: str = os.getenv("MP_ACCESS_TOKEN", "")
    mp_webhook_secret: str = os.getenv("MP_WEBHOOK_SECRET", "")

    encryption_secret: str = os.getenv("ENCRYPTION_SECRET", "")

    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    public_base_url: str = os.getenv("PUBLIC_BASE_URL", "")


settings = Settings()