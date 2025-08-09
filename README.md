# 🤖 Bot de Vendas Automatizadas - Sistema Completo

Sistema completo de vendas automatizadas via Telegram com dois bots integrados: **Bot Administrativo** e **Bot da Loja**.

## 📋 Funcionalidades Principais

### 🏪 Bot da Loja
- ✅ Menu principal intuitivo com emojis personalizados
- ✅ Catálogo de produtos organizados por categorias
- ✅ Sistema de compra automatizado
- ✅ Recarga de saldo via PIX com QR Code
- ✅ Sistema de afiliados (50% de comissão)
- ✅ Perfil do usuário com histórico
- ✅ Suporte técnico integrado
- ✅ Busca de serviços
- ✅ Notificações automáticas

### 🔧 Bot Administrativo
- ✅ Painel completo de administração
- ✅ Gerenciamento de categorias e serviços
- ✅ Controle de estoque em tempo real
- ✅ Gestão de usuários e permissões
- ✅ Relatórios financeiros detalhados
- ✅ Estatísticas de vendas
- ✅ Logs do sistema
- ✅ Sincronização entre bots
- ✅ Alertas de estoque baixo

### 💳 Sistema de Pagamentos
- ✅ Integração com Mercado Pago
- ✅ Pagamentos via PIX
- ✅ QR Code automático
- ✅ Verificação de status em tempo real
- ✅ Webhook para confirmações
- ✅ Histórico de transações

### 🔐 Segurança
- ✅ Criptografia de dados sensíveis
- ✅ Rate limiting e proteção contra spam
- ✅ Detecção de atividades suspeitas
- ✅ Logs de segurança
- ✅ Autenticação JWT
- ✅ Validação de entrada de dados

## 🚀 Instalação e Configuração

### Pré-requisitos
- Python 3.9+
- MySQL 8.0+
- Conta no Mercado Pago (para PIX)
- Tokens dos bots do Telegram

### 1. Clone o repositório
```bash
git clone <repository-url>
cd bot-vendas-automatizadas
```

### 2. Instale as dependências
```bash
pip install -r requirements.txt
```

### 3. Configure o banco de dados
```sql
CREATE DATABASE vendas_bot CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 4. Configure as variáveis de ambiente
```bash
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

### 5. Configure o arquivo config.py
Edite o arquivo `config.py` com suas configurações específicas:
- Tokens dos bots
- Configurações do banco de dados
- IDs dos administradores
- Chaves do Mercado Pago

### 6. Inicialize o banco de dados
```python
python -c "from database import db; db.connect(); db.create_tables()"
```

## 🎯 Como Usar

### Executar o Bot Administrativo
```bash
python admin_bot.py
```

### Executar o Bot da Loja
```bash
python shop_bot.py
```

### Executar ambos simultaneamente
```bash
# Terminal 1
python admin_bot.py

# Terminal 2
python shop_bot.py
```

## 📱 Comandos dos Bots

### Bot Administrativo
- `/start` ou `/adm` - Acessa o painel administrativo
- Apenas usuários com ID listado em `ADMIN_IDS` têm acesso

### Bot da Loja
- `/start` - Inicia o bot e mostra o menu principal
- `/start ref_USERID` - Inicia com referência de afiliado

## 🗂️ Estrutura do Projeto

```
├── admin_bot.py          # Bot administrativo
├── shop_bot.py           # Bot da loja
├── database.py           # Sistema de banco de dados
├── payment_system.py     # Sistema de pagamentos PIX
├── security.py           # Sistema de segurança
├── sync_system.py        # Sincronização entre bots
├── config.py             # Configurações do sistema
├── requirements.txt      # Dependências Python
├── .env.example         # Exemplo de variáveis de ambiente
└── README.md            # Esta documentação
```

## 🔧 Configuração Detalhada

### Tokens dos Bots
1. Crie dois bots no @BotFather
2. Copie os tokens para o `config.py`:
   - `ADMIN_BOT_TOKEN` - Token do bot administrativo
   - `SHOP_BOT_TOKEN` - Token do bot da loja

### Mercado Pago
1. Crie uma conta no Mercado Pago
2. Acesse o painel de desenvolvedores
3. Obtenha suas credenciais:
   - Access Token
   - Public Key
4. Configure no arquivo `config.py`

### Banco de Dados
O sistema criará automaticamente as seguintes tabelas:
- `users` - Usuários do sistema
- `categories` - Categorias de produtos
- `services` - Serviços/produtos
- `accounts` - Contas/logins para venda
- `transactions` - Transações financeiras
- `commissions` - Comissões de afiliados
- `logs` - Logs do sistema
- `settings` - Configurações

## 👥 Sistema de Afiliados

### Como funciona
1. Usuário compartilha link: `t.me/seu_bot?start=ref_USERID`
2. Novos usuários se cadastram pelo link
3. Afiliado ganha 50% de comissão em todas as recargas
4. Comissão é creditada automaticamente

### Configuração
- Taxa de comissão: `COMMISSION_RATE` (padrão: 0.5 = 50%)
- Comissões são pagas automaticamente após confirmação do pagamento

## 💰 Sistema Financeiro

### Fluxo de Pagamento
1. Usuário escolhe valor de recarga
2. Sistema gera PIX via Mercado Pago
3. QR Code é enviado ao usuário
4. Usuário paga via app bancário
5. Webhook confirma pagamento
6. Saldo é creditado automaticamente
7. Comissão de afiliado é processada (se aplicável)

### Limites
- Recarga mínima: R$ 10,00
- Recarga máxima: R$ 1.000,00
- Configurável via `MIN_RECHARGE_AMOUNT` e `MAX_RECHARGE_AMOUNT`

## 🛡️ Segurança

### Medidas Implementadas
- **Criptografia**: Dados sensíveis criptografados com Fernet
- **Rate Limiting**: Máximo 5 tentativas por 5 minutos
- **Detecção de Fraudes**: Análise de padrões suspeitos
- **Logs Detalhados**: Todas as ações são registradas
- **Validação de Entrada**: Sanitização de dados de entrada
- **Autenticação JWT**: Tokens seguros para sessões

### Configurações de Segurança
```python
MAX_ATTEMPTS = 5          # Máximo de tentativas falhas
LOCKOUT_DURATION = 300    # Tempo de bloqueio (segundos)
ENCRYPTION_KEY = "..."    # Chave de criptografia (32 bytes)
```

## 📊 Relatórios e Estatísticas

### Bot Administrativo oferece:
- Vendas por período
- Produtos mais vendidos
- Usuários mais ativos
- Estatísticas financeiras
- Relatórios de estoque
- Logs de segurança

### Dados disponíveis:
- Faturamento total
- Número de vendas
- Ticket médio
- Comissões pagas
- Saldo total dos usuários

## 🔄 Sincronização

### Sistema de Sync
- Sincronização automática a cada 60 segundos
- Cache inteligente para performance
- Notificações de mudanças
- Alertas de estoque baixo
- Detecção de alterações via hash

### Dados Sincronizados
- Categorias e serviços
- Estoque disponível
- Configurações do sistema
- Estatísticas de usuários

## 📝 Logs e Monitoramento

### Tipos de Logs
- **Ações do usuário**: Compras, recargas, navegação
- **Eventos de segurança**: Tentativas suspeitas, bloqueios
- **Sistema**: Erros, sincronização, performance
- **Financeiro**: Pagamentos, comissões, reembolsos

### Localização dos Logs
- Banco de dados: Tabela `logs`
- Arquivo: `bot_logs.log` (configurável)
- Console: Logs em tempo real

## ⚙️ Manutenção

### Backup do Banco
```bash
mysqldump -u username -p vendas_bot > backup_$(date +%Y%m%d).sql
```

### Limpeza de Logs Antigos
```sql
DELETE FROM logs WHERE created_at < DATE_SUB(NOW(), INTERVAL 90 DAY);
```

### Monitoramento de Performance
- Verificar uso de CPU e memória
- Monitorar conexões do banco
- Acompanhar tempo de resposta

## 🐛 Solução de Problemas

### Problemas Comuns

#### Bot não responde
1. Verificar se o token está correto
2. Verificar conexão com internet
3. Verificar logs de erro

#### Pagamentos não processam
1. Verificar credenciais do Mercado Pago
2. Verificar webhook configurado
3. Verificar logs de pagamento

#### Banco de dados
1. Verificar conexão
2. Verificar permissões do usuário
3. Verificar se as tabelas existem

### Logs de Debug
Ativar logs detalhados:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📞 Suporte

### Configurações de Suporte
Edite no arquivo `config.py`:
```python
SUPPORT_CONTACT = "@seu_suporte"
SUPPORT_PHONE = "+5511999999999"
SUPPORT_EMAIL = "suporte@seudominio.com"
```

## 🔄 Atualizações

### Como atualizar
1. Fazer backup do banco de dados
2. Baixar nova versão
3. Instalar novas dependências: `pip install -r requirements.txt`
4. Executar migrações se necessário
5. Reiniciar os bots

## 📄 Licença

Este projeto é fornecido como está, para uso educacional e comercial.

## 🤝 Contribuição

Para contribuir com o projeto:
1. Fork o repositório
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

---

## 🎯 Recursos Avançados

### Multilinguismo
O sistema está preparado para suporte a múltiplos idiomas:
```python
LANGUAGES = {
    'pt': 'Português',
    'en': 'English'
}
```

### Webhooks
Sistema completo de webhooks para integrações:
- Confirmação de pagamentos
- Notificações de vendas
- Alertas de sistema

### API REST (Futuro)
Estrutura preparada para API REST para integrações externas.

### Escalabilidade
- Sistema preparado para múltiplos bots
- Cache inteligente para performance
- Otimizações de banco de dados

---

**Desenvolvido com ❤️ para automatizar vendas no Telegram**

Para dúvidas ou suporte, consulte a documentação ou entre em contato.
