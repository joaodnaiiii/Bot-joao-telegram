import os
from dataclasses import dataclass


@dataclass
class Settings:
    callmebot_apikey: str = os.getenv("CALLMEBOT_APIKEY", "")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./data.db")


def get_settings() -> Settings:
    return Settings()
