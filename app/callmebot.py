from typing import Optional
import httpx
import urllib.parse


class CallMeBotClient:
    base_url: str = "https://api.callmebot.com/whatsapp.php"

    def __init__(self, apikey: str) -> None:
        if not apikey:
            raise ValueError("CALLMEBOT_APIKEY não configurado")
        self.apikey = apikey

    async def send_text(self, to_phone_e164: str, text: str, timeout_seconds: float = 15.0) -> str:
        params = {
            "phone": to_phone_e164,
            "text": text,
            "apikey": self.apikey,
        }

        # CallMeBot exige texto url-encoded; httpx faz isso automaticamente via params
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            response = await client.get(self.base_url, params=params)
            # Não propagar erro 5xx do CallMeBot; retornar texto bruto para evitar quebra do fluxo
            try:
                response.raise_for_status()
            except Exception:
                pass
            return response.text
