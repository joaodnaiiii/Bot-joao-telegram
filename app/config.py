import os
from dataclasses import dataclass
from dotenv import load_dotenv


# carrega variáveis do arquivo .env se existir
load_dotenv()


@dataclass
class Settings:
    callmebot_apikey: str = os.getenv("CALLMEBOT_APIKEY", "")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./data.db")
    support_name: str = os.getenv("SUPPORT_NAME", "JOÃO")
    support_number: str = os.getenv("SUPPORT_NUMBER", "5544998312326")


def get_settings() -> Settings:
    return Settings()
