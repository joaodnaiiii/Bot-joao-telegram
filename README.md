# JOÃOZINHO STORE BOT – WhatsApp (FastAPI)

Bot de vendas para WhatsApp com menus interativos, recarga via PIX, compras de assinaturas premium, conta do usuário, histórico e proteção contra flood.

## Requisitos

- Python 3.10+
- Bibliotecas: FastAPI, Uvicorn, SQLAlchemy, httpx, APScheduler, python-dotenv
- Banco de dados: SQLite (padrão) ou PostgreSQL
- Conta no WhatsApp Cloud API (Meta) com `PHONE_NUMBER_ID` e `WHATSAPP_TOKEN`
- Provedor PIX (mock incluso). Suporte a webhooks de provedor (ex.: EFI/Gerencianet, OpenPix) via endpoint `/pix/webhook`

## Variáveis de ambiente

- `WHATSAPP_TOKEN`: Token de acesso do WhatsApp Cloud API
- `WHATSAPP_PHONE_NUMBER_ID`: ID do número do WhatsApp Cloud API
- `WHATSAPP_VERIFY_TOKEN`: Token para validação de webhook (GET)
- `DATABASE_URL`: URL do banco (ex.: `sqlite:///./data.db` ou `postgresql+psycopg2://user:pass@host:5432/db`)
- `PIX_PROVIDER`: `mock` (padrão) ou `efi`
- `PIX_WEBHOOK_SECRET`: Segredo para autenticar webhooks de PIX (usado no mock e recomendado para provedores)
- `SUPPORT_NAME`: Nome do responsável (ex.: `JOÃO`)
- `SUPPORT_NUMBER`: Telefone do suporte, no formato E.164 (ex.: `5544998312326`)

## Rodando localmente

1. Crie um `.env` com as variáveis acima.
2. Instale dependências:
   ```bash
   pip install -r requirements.txt
   ```
3. Inicie a API:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
4. Configure o webhook do WhatsApp para `https://SEU_HOST/webhook`.

### Teste rápido com CallMeBot

1. Copie `.env.example` para `.env` e ajuste `CALLMEBOT_APIKEY` se necessário.
2. Envie uma mensagem teste:
   ```bash
   curl -X POST http://localhost:8000/send \
     -H 'Content-Type: application/json' \
     -d '{"to":"554498312326", "text":"This is a test"}'
   ```
3. Para enviar o menu de demonstração:
   ```bash
   curl -X POST 'http://localhost:8000/send/menu-demo?to=554498312326'
   ```

## Fluxos implementados

- Menu principal com botões:
  - Adicionar Saldo (PIX com valores R$5, R$10, R$20 e valor personalizado)
  - Assinaturas Premium (4 produtos configuráveis)
  - Área do Associado
  - Contato do Suporte
- PIX:
  - Geração de cobrança com QR Code/código (mock gera código e expiração em 30 min)
  - Notificação automática por webhook quando pago (ou expiração)
  - Crédito em até 1 minuto após pagamento
- Assinaturas:
  - Lista de 4 produtos com preço e estoque
  - Se saldo insuficiente: mensagem de recarga
  - Se saldo suficiente: compra imediata e entrega (credenciais simuladas)
- Minha Conta:
  - Dados: Nome, ID, Número, Indicador, Cargo, Saldo, Bônus
  - Minhas Compras (envio como texto; envio de documento requer mídia no Cloud API)
  - Resgatar Saldo (converter bônus em saldo com confirmação)
- Área do Associado: confirmações contextuais (ex.: conversão de bônus)
- Suporte: mensagem com contato
- Proteção contra flood: bloqueio cumulativo de 6s

## Observações

- Para reconhecimento automático de PIX em produção, aponte o webhook do seu provedor para `POST /pix/webhook` e implemente o adaptador do provedor (vide `app/pix.py`).
- Para envio de documentos no WhatsApp, suba o arquivo via Graph API e envie usando `media_id`.
- Telegram não é utilizado nesta versão. O arquivo `bot.py` antigo foi mantido apenas como referência.
