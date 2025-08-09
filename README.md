## Bot de Vendas Automatizadas (Telegram)

Dois bots Telegram (loja e administração) com pagamentos via Pix (Mercado Pago), estoque de logins, afiliados e multilíngue.

### Requisitos
- Python 3.10+

### Configuração
1. Copie `.env.example` para `.env` e preencha:
   - `SHOP_BOT_TOKEN` e `ADMIN_BOT_TOKEN`
   - `PAYMENT_PROVIDER` (`mock` para testes; `mercadopago` em produção)
   - `MP_ACCESS_TOKEN` ao usar `mercadopago`
   - `DATABASE_URL` (padrão SQLite)
   - `PUBLIC_BASE_URL` se for usar webhook
2. Instalar dependências:
   ```bash
   pip install -r requirements.txt
   ```

### Executar
- Somente bots (long polling):
  ```bash
  python -m src.run_all
  ```
- Somente bot da loja:
  ```bash
  python -m src.bots.shop_bot
  ```
- Somente bot admin:
  ```bash
  python -m src.bots.admin_bot
  ```
- API (webhook/health) + scheduler:
  ```bash
  uvicorn src.server:app --host 0.0.0.0 --port 8000
  ```

### Principais Funcionalidades
- Loja: Serviços com estoque, compra via Pix com QRCode, entrega automática, recarga, perfil, pesquisa, multilíngue.
- Admin: CRUD de serviços, upload de estoque, usuários e permissões, relatórios, alertas.
- Afiliados: Link de indicação via `/start ref_<id>`, comissão configurável.

### Observações
- Produção: use Postgres em `DATABASE_URL` e `PAYMENT_PROVIDER=mercadopago`.
- Configure o webhook Pix do Mercado Pago apontando para `/webhooks/mercadopago`.
