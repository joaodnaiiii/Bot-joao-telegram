from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .db import SessionLocal
from .models import FloodState, Product, Purchase
from .flow import (
    ensure_user,
    get_products,
    render_products_list,
    render_product_detail,
    create_pix_for_user,
    render_pix_message,
    MAIN_MENU,
    render_add_saldo_menu,
    render_account,
    render_support,
    render_flood_block,
)
from .callmebot import CallMeBotClient
from .config import get_settings


router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


settings = get_settings()
callme_client: Optional[CallMeBotClient] = (
    CallMeBotClient(apikey=settings.callmebot_apikey) if settings.callmebot_apikey else None
)


@router.post("/message")
async def receive_message(phone: str, text: str, db: Session = Depends(get_db)):
    if not callme_client:
        return {"error": "CALLMEBOT_APIKEY não configurado"}

    # antiflood: 6s cumulativo
    flood = db.get(FloodState, phone)
    now = datetime.utcnow()
    if flood:
        remain = (flood.last_violation_at + timedelta(seconds=flood.penalty_seconds)) - now
        if remain.total_seconds() > 0:
            # não enviar mensagem em caso de bloqueio para evitar 503 e loops
            return {"status": "blocked", "retry_after": int(remain.total_seconds())}

        flood.penalty_seconds = min(flood.penalty_seconds + 6, 60)
        flood.last_violation_at = now
    else:
        flood = FloodState(phone=phone, penalty_seconds=6, last_violation_at=now)
        db.add(flood)
    db.commit()

    user = ensure_user(db, phone)
    lower = text.strip().lower()

    # comandos básicos
    if lower in {"menu", "inicio", "início", "start", "voltar"}:
        await callme_client.send_text(phone, MAIN_MENU.format(phone=phone, balance=user.balance))
        return {"status": "ok"}

    if lower.startswith("💸") or lower.startswith("adicionar saldo"):
        await callme_client.send_text(phone, render_add_saldo_menu())
        return {"status": "ok"}

    if lower in {"pix r$ 5,00", "pix r$ 10,00", "pix r$ 20,00"} or lower.startswith("pix r$"):
        value_map = {"pix r$ 5,00": 5.0, "pix r$ 10,00": 10.0, "pix r$ 20,00": 20.0}
        amount = value_map.get(lower)
        if amount is None:
            # tentar parsear: pix r$ X,XX
            try:
                raw = lower.replace("pix r$", "").replace(" ", "").replace(",", ".")
                amount = float(raw)
            except Exception:
                amount = 10.0

        invoice = create_pix_for_user(db, user, amount)
        msg = render_pix_message(invoice)
        await callme_client.send_text(phone, msg)
        return {"status": "ok"}

    if "digite outro valor" in lower:
        await callme_client.send_text(phone, "Envie: PIX R$ 12,34 (exemplo) para gerar o pagamento.")
        return {"status": "ok"}

    if lower.startswith("🛍️") or lower.startswith("assinaturas"):
        products = get_products(db)
        await callme_client.send_text(phone, render_products_list(products))
        return {"status": "ok"}

    if lower.isdigit():
        pid = int(lower)
        product = db.get(Product, pid)
        if product:
            await callme_client.send_text(phone, render_product_detail(user, product))
            return {"status": "ok"}

    if lower.startswith("comprar "):
        try:
            pid = int(lower.split()[1])
        except Exception:
            pid = None
        if pid:
            product = db.get(Product, pid)
            if not product:
                await callme_client.send_text(phone, "Produto não encontrado.")
            else:
                if user.balance < product.price:
                    await callme_client.send_text(
                        phone,
                        "*❌ Saldo Insuficiente!*\n\nSeu saldo atual não é suficiente. Faça uma recarga! 💰",
                    )
                elif product.stock <= 0:
                    await callme_client.send_text(phone, "Produto sem estoque no momento.")
                else:
                    user.balance -= product.price
                    product.stock -= 1
                    purchase = Purchase(
                        user_id=user.id,
                        product_id=product.id,
                        price_paid=product.price,
                        delivered_text=(
                            f"Compra de {product.name} confirmada!\n\n"
                            "Como usar: baixe o app na App Store/Play Store, faça login com as credenciais enviadas.\n\n"
                            "Email: cliente@example.com\nSenha: 123456"
                        ),
                    )
                    db.add(purchase)
                    db.commit()
                    await callme_client.send_text(phone, purchase.delivered_text)
            return {"status": "ok"}

    if lower.startswith("minha conta") or lower.startswith("minha"):
        await callme_client.send_text(phone, render_account(user))
        return {"status": "ok"}

    if lower.startswith("minhas compras"):
        if len(user.purchases) == 0:
            await callme_client.send_text(phone, "Você ainda não possui compras.")
        else:
            lines = []
            for p in user.purchases:
                lines.append(
                    f"{p.created_at:%d/%m/%Y %H:%M} - {p.product.name} - R$ {p.price_paid:.2f}"
                )
            await callme_client.send_text(phone, "Suas compras:\n" + "\n".join(lines))
        return {"status": "ok"}

    if lower.startswith("resgatar saldo") or lower.startswith("resgatar"):
        if user.bonus <= 0:
            await callme_client.send_text(phone, "*⏳ Você possui R$ 0,00 em bônus.*\nInforme a quantidade que deseja converter em saldo.\nVocê tem *80 segundos* para responder.")
        else:
            await callme_client.send_text(
                phone,
                f"*⏳ Você possui R$ {user.bonus:.2f} em bônus.*\nInforme a quantidade que deseja converter em saldo.\nVocê tem *80 segundos* para responder.",
            )
        return {"status": "ok"}

    if lower.startswith("área do associado") or lower.startswith("area do associado"):
        await callme_client.send_text(phone, "❓ Confirmar Conversão \n*_____________________________*\n\nDeseja converter R$: NaN em saldo?\nResponda CONFIRMAR ou CANCELAR.")
        return {"status": "ok"}

    if lower.startswith("confirmar"):
        # simples: converte tudo em bônus
        if user.bonus > 0:
            user.balance += user.bonus
            user.bonus = 0.0
            db.commit()
            await callme_client.send_text(phone, "Conversão realizada com sucesso!")
        else:
            await callme_client.send_text(phone, "Sem bônus para converter.")
        return {"status": "ok"}

    if lower.startswith("cancelar"):
        await callme_client.send_text(phone, "Operação cancelada.")
        return {"status": "ok"}

    if lower.startswith("suporte") or lower.startswith("contato"):
        await callme_client.send_text(phone, render_support(settings.__dict__.get("support_name", "JOÃO"), settings.__dict__.get("support_number", "5544998312326")))
        return {"status": "ok"}

    # default -> menu
    await callme_client.send_text(phone, MAIN_MENU.format(phone=phone, balance=user.balance))
    return {"status": "ok"}
