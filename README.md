# JOÃOZINHO STORE BOT (WhatsApp)

Bot de vendas para WhatsApp com carteira, PIX (mock/placeholder Efí), assinaturas premium, extrato de compras, anti-flood e suporte.

## Requisitos
- Node.js 18+

## Configuração
1. Copie `.env.example` para `.env` e ajuste as variáveis (opcionais):
```
cp .env.example .env
```
2. Instale dependências:
```
npm i
```

## Executar
```
npm run dev
```
Escaneie o QR Code no terminal com o WhatsApp do bot.

## Fluxos implementados
- Menu principal: Adicionar Saldo, Assinaturas Premium, Área do Associado, Suporte
- Adicionar Saldo: valores R$5, R$10, R$20 e valor personalizado
- Geração de cobrança (PIX mock): QR code + código copia e cola, expiração em 30min, confirmação/manual via webhook mock
- Assinaturas Premium: lista de 4 produtos, detalhe e compra com débito de saldo
- Área do Associado: Minha conta, Minhas compras (gera texto), Resgatar saldo (converter bônus → saldo)
- Suporte: mensagem com nome e número configurado
- Anti-flood: bloqueio por 6s entre interações

## Observações
- O provedor de PIX é um mock local por padrão. Para usar Efí, implemente um provedor `efiProvider.js` lendo as variáveis do `.env` e integre em `src/index.js`.
- Banco de dados: `better-sqlite3` em `/workspace/data.sqlite`.