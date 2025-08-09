from typing import Dict


PT: Dict[str, str] = {
    "menu_services": "🛍️ Logins | Contas Premium",
    "menu_profile": "👤 Perfil",
    "menu_topup": "💳 Recarga Pix",
    "menu_support": "🛟 Suporte",
    "menu_search": "🔎 Pesquisar Serviço",
    "menu_language": "🌐 Idioma",
    "welcome": "Bem-vindo! Escolha uma opção:",
    "choose_language": "Escolha seu idioma:",
    "lang_pt": "🇧🇷 Português",
    "lang_en": "🇺🇸 English",
    "no_services": "Nenhum serviço disponível no momento.",
    "select_service": "Selecione um serviço:",
    "service_details": "{name}\nPreço: R$ {price}\n{desc}",
    "buy": "🛒 Comprar",
    "back": "⬅️ Voltar",
    "payment_qr": "Pague via Pix usando o QRCode ou copie o código abaixo.",
    "waiting_payment": "Aguardando pagamento...",
    "paid": "Pagamento confirmado!",
    "delivered": "Aqui estão seus dados:",
    "out_of_stock": "Estoque insuficiente para este serviço.",
    "profile": "Saldo: R$ {balance}\nCompras: {orders}\nRecargas: {topups}",
    "topup_how_much": "Informe o valor da recarga (em reais):",
    "invalid_amount": "Valor inválido.",
    "support_info": "Entre em contato: @seu_suporte",
    "search_prompt": "Digite o nome do serviço para procurar:",
    "search_results": "Resultados:",
}

EN: Dict[str, str] = {
    "menu_services": "🛍️ Premium Accounts",
    "menu_profile": "👤 Profile",
    "menu_topup": "💳 Top-up Pix",
    "menu_support": "🛟 Support",
    "menu_search": "🔎 Search Service",
    "menu_language": "🌐 Language",
    "welcome": "Welcome! Choose an option:",
    "choose_language": "Choose your language:",
    "lang_pt": "🇧🇷 Portuguese",
    "lang_en": "🇺🇸 English",
    "no_services": "No services available.",
    "select_service": "Select a service:",
    "service_details": "{name}\nPrice: R$ {price}\n{desc}",
    "buy": "🛒 Buy",
    "back": "⬅️ Back",
    "payment_qr": "Pay with Pix using the QRCode or copy the code below.",
    "waiting_payment": "Waiting for payment...",
    "paid": "Payment received!",
    "delivered": "Here are your credentials:",
    "out_of_stock": "Insufficient stock for this service.",
    "profile": "Balance: R$ {balance}\nOrders: {orders}\nTop-ups: {topups}",
    "topup_how_much": "Enter top-up amount (BRL):",
    "invalid_amount": "Invalid amount.",
    "support_info": "Contact: @your_support",
    "search_prompt": "Type a service name to search:",
    "search_results": "Results:",
}


def t(lang: str, key: str, **kwargs) -> str:
    table = PT if lang.startswith("pt") else EN
    txt = table.get(key, key)
    try:
        return txt.format(**kwargs)
    except Exception:
        return txt