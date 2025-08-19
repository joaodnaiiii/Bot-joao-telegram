from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .config import get_settings
from .callmebot import CallMeBotClient
from .db import init_db
from .inbound import router as inbound_router
from .pix_webhook import router as pix_router


class SendMessageRequest(BaseModel):
    to: str = Field(..., description="Telefone do destinatário no formato E.164, ex.: 554491234567")
    text: str = Field(..., description="Texto da mensagem a ser enviada")


app = FastAPI(title="JOÃOZINHO STORE BOT (CallMeBot)")
settings = get_settings()
callme_client = CallMeBotClient(apikey=settings.callmebot_apikey) if settings.callmebot_apikey else None


@app.get("/")
def root():
    return {"status": "ok"}


@app.post("/send")
async def send_message(payload: SendMessageRequest):
    if not callme_client:
        raise HTTPException(status_code=500, detail="CALLMEBOT_APIKEY não configurado")
    try:
        result = await callme_client.send_text(payload.to, payload.text)
        return {"result": result}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@app.post("/send/menu-demo")
async def send_menu_demo(to: str):
    if not callme_client:
        raise HTTPException(status_code=500, detail="CALLMEBOT_APIKEY não configurado")

    menu_text = (
        "🤖 JOÃOZINHO STORE BOT\n\n"
        "ℹ️ Seus Dados:\n"
        "💠 Número: {num}\n💸 Saldo Atual: R$ 0,00\n\n"
        "Escolha uma opção:\n\n"
        "💸 Adicionar Saldo\n"
        "🛍️ Assinaturas Premium\n\n"
        "💼 Area do Associado\n\n"
        "🆘 Contato do Suporte"
    ).format(num=to)

    try:
        result = await callme_client.send_text(to, menu_text)
        return {"result": result}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@app.on_event("startup")
def on_startup():
    init_db()


app.include_router(inbound_router, prefix="/inbound", tags=["inbound"])
app.include_router(pix_router, prefix="/pix", tags=["pix"])
