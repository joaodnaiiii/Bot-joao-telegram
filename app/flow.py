from __future__ import annotations

from datetime import datetime
from sqlalchemy.orm import Session

from .models import User, Product, PixInvoice, Purchase
from .pix import generate_mock_pix


MAIN_MENU = (
    "🤖 JOÃOZINHO STORE BOT\n\n"
    "ℹ️ Seus Dados:\n"
    "💠 Número: {phone}\n💸 Saldo Atual: R$ {balance:.2f}\n\n"
    "Escolha uma opção (responda o número):\n"
    "1) 💸 Adicionar Saldo\n"
    "2) 🛍️ Assinaturas Premium\n"
    "3) 💼 Area do Associado\n"
    "4) 🆘 Contato do Suporte"
)


def ensure_user(db: Session, phone: str) -> User:
    user = db.query(User).filter(User.phone == phone).first()
    if not user:
        user = User(phone=phone)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def get_products(db: Session) -> list[Product]:
    products = db.query(Product).order_by(Product.id.asc()).all()
    if len(products) == 0:
        seed_products = [
            ("Netflix Premium 1 Tela", 10.00, 50),
            ("Spotify Family", 15.00, 30),
            ("HBO Max 4K", 20.00, 20),
            ("Disney+", 12.00, 40),
        ]
        for name, price, stock in seed_products:
            db.add(Product(name=name, price=price, stock=stock, description="Assinatura digital", warranty_days=30))
        db.commit()
        products = db.query(Product).order_by(Product.id.asc()).all()
    return products


def render_products_list(products: list[Product]) -> str:
    lines = ["🥇 Assinaturas Premium (escolha o número):\n"]
    for idx, p in enumerate(products, start=1):
        lines.append(f"{idx}) {p.name} - R$ {p.price:.2f} (Estoque: {p.stock})")
    lines.append("\nResponda o número para ver detalhes.")
    return "\n".join(lines)


def render_product_detail(user: User, product: Product) -> str:
    if user.balance < product.price:
        return (
            "*❌ Saldo Insuficiente!*\n\n"
            "Seu saldo atual não é suficiente para concluir esta compra. Faça uma *recarga* e tente novamente! 💰"
        )

    return (
        "◎ ══════ ❈ ══════ ◎\n"
        f"⚜️ACESSO: {product.name} ⚜️\n\n"
        f"💵| Preço: R$ {product.price:.2f}\n"
        f"💼| Saldo Atual: {user.balance:.2f}\n"
        f"📥| Estoque Disponível: {product.stock}\n\n"
        "🗒 Descrição: Aviso Importante:\n"
        "Informamos que não realizamos reembolsos via Pix, apenas em créditos no bot, correspondendo aos dias restantes até o vencimento.\n"
        "Agradecemos pela compreensão e desejamos boas compras!\n\n"
        "Obs: O prazo de entrega é até 24 horas.\n"
        "Obs: ERRO DE 12 MESES OU ERRO DE CONVITE QUE NAO CHEGOU, AVISAR EM ATÉ 2 DIAS NO MÁXIMO, APÓS ISSO PERDE SUPORTE E QUALQUER TIPO DE AJUDA.\n"
        "Obs: Olhe atentamente a o texto da compra.\n\n"
        "♻️ Garantia: 30\n"
        "◎ ══════ ❈ ══════ ◎\n\n"
        "Responda 1) 🛒 Comprar  ou  0) ⬅️ Voltar"
    )


def render_add_saldo_menu() -> str:
    return (
        "💸 MENU DE OPÇÃO DE PIX 💸\n\n"
        "Escolha uma opção (responda o número):\n"
        "1) 💠 PIX R$ 5,00\n"
        "2) 💠 PIX R$ 10,00\n"
        "3) 💠 PIX R$ 20,00\n"
        "4) 💠 DIGITE OUTRO VALOR"
    )


def create_pix_for_user(db: Session, user: User, amount: float) -> PixInvoice:
    charge = generate_mock_pix(amount)
    invoice = PixInvoice(
        user_id=user.id,
        amount=amount,
        code=charge.code,
        qrcode_url=charge.qrcode_url,
        status="pending",
        expires_at=charge.expires_at,
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice


def render_pix_message(invoice: PixInvoice) -> str:
    venc = invoice.expires_at.strftime("%d/%m/%Y às %H:%M:%S")
    return (
        "*⏳ Gerando PIX...*\n\n"
        "Aguarde um momento! 💰\n\n"
        "*💰 ADICIONAR SALDO COM PIX AUTOMÁTICO 💠*\n\n"
        "⚠️ Você está prestes a adicionar saldo ao bot!\n\n"
        "Escaneie o *QR Code* acima ou utilize o *código PIX* enviado abaixo.\n\n"
        "O PIX expira em *30 minutos*, pague dentro do prazo.\n\n"
        "O saldo será creditado em até *1 \nminuto* após o pagamento.\n\n"
        "*⚠️ ADICIONE APENAS O QUE FOR USAR!*\n"
        "_Não realizamos reembolsos._\n\n"
        "━━━━━━━━❪❃❫━━━━━━━━\n\n"
        f"*🆔 ID da Compra:* {invoice.id}\n"
        f"*💰 Valor:* R$ {invoice.amount:.2f}\n"
        f"*📅 Vencimento:* {venc}\n\n"
        "━━━━━━━━❪❃❫━━━━━━━━\n\n"
        "*🔑 O código PIX foi enviado abaixo para facilitar o pagamento!*\n\n"
        f"{invoice.code}"
    )


def render_account(user: User) -> str:
    return (
        "🗒️ SUA CONTA\n"
        f"👤 Nome: {user.name or '-'}\n"
        f"🆔 Telegram ID: -\n"
        f"📞 Número: {user.phone}\n\n"
        f"\n📢 Indicador: {user.referrer or '-'}\n"
        f"Cargo: {user.role}\n"
        f"Saldo: R$ {user.balance:.2f}\n"
        f"Bônus: R$ {user.bonus:.2f}\n\n"
        "Opções:\n"
        "🛍️ Minhas Compras\n"
        "💰 Resgatar Saldo"
    )


def render_support(name: str, number: str) -> str:
    return (
        "*👤 CONTATO DO SUPORTE 👤*\n\n"
        "*⚠️ Este é o número do responsável ou suporte deste bot.*\n\n"
        "*⚠️ Dúvidas sobre o material vendido?* Entre em contato apenas com este número!\n\n"
        f"*{name}* - meu número {number}"
    )


def render_flood_block(seconds: int) -> str:
    return (
        "*⚠️ Atenção!*\n\n"
        "Pare de floodar! Suas solicitações serão ignoradas pelos próximos *{s} segundos* (acumulativo). ⏳"
    ).format(s=seconds)
