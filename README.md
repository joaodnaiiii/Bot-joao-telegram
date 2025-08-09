# 🏪 Joazinho Store Bot System

Um sistema completo de bot para vendas automatizadas de logins e serviços digitais no Telegram, com painel administrativo avançado e interface de loja personalizada.

## ✨ Características Principais

### 🛒 Bot da Loja (Store Bot)
- **Interface Personalizada**: Menu principal com layout específico e imagem personalizada
- **Catálogo de Produtos**: Exibição organizada de serviços com preços e estoque
- **Sistema de Pagamento PIX**: Integração com PushinPay para pagamentos automáticos
- **Sistema de Perfil**: Visualização de saldo, histórico de compras e estatísticas
- **Ranking Interativo**: Rankings de serviços, recargas, compras e saldos
- **Sistema de Afiliados**: Links de indicação com comissões automáticas
- **Suporte Integrado**: Redirecionamento direto para canais de suporte
- **Pesquisa de Serviços**: Busca inteligente por produtos
- **Sistema de Alertas**: Notificações de reabastecimento de produtos
- **Multilíngue**: Suporte para português e inglês

### 👨‍💼 Bot Administrativo (Admin Bot)
- **Dashboard Completo**: Métricas de negócio em tempo real
- **Gerenciamento de Serviços**: Adicionar, remover e configurar produtos
- **Gerenciamento de Usuários**: Controle completo de usuários e permissões
- **Configurações PIX**: Gestão de pagamentos e tokens
- **Sistema de Logs**: Monitoramento de atividades e segurança
- **Relatórios Financeiros**: Análise de vendas e receitas
- **Sistema de Backup**: Proteção de dados
- **Configurações Avançadas**: Personalização completa do sistema

## 🚀 Instalação Rápida

### 1. Pré-requisitos
```bash
- Python 3.8+
- MySQL/MariaDB
- Tokens dos bots do Telegram
```

### 2. Instalação
```bash
# Clone o repositório
git clone https://github.com/seu-usuario/joazinho-store-bot.git
cd joazinho-store-bot

# Instale as dependências
pip install -r requirements.txt
```

### 3. Configuração
1. Edite o arquivo `config.py` com suas configurações:
   - Tokens dos bots
   - Configurações do banco de dados
   - Chaves de pagamento
   - IDs dos administradores

2. Execute o setup inicial:
```bash
python setup.py
```

### 4. Executar o Sistema
```bash
# Executar ambos os bots
python run_bots.py

# Ou executar separadamente
python store_bot.py  # Bot da loja
python admin_bot.py  # Bot administrativo
```

## 🔧 Configuração Detalhada

### Tokens dos Bots
- **Store Bot**: `8322262425:AAH3k6l9X6u1M4_FHNzG5HHLmELnfO6xqkM`
- **Admin Bot**: `7405988960:AAEQWzK9-GMiRDSGGc_yLvAq3KMYvkL6DI0`

### Banco de Dados
Configure sua string de conexão MySQL em `config.py`:
```python
DATABASE_URL = 'mysql+mysqlconnector://usuario:senha@localhost/joazinho_store'
```

### Pagamentos PIX
- Integração com PushinPay
- Geração automática de QR Codes
- Verificação de pagamentos em tempo real
- Suporte a webhooks

## 📱 Como Usar

### Para Clientes (Store Bot)

#### Comandos Principais:
- `/start` - Iniciar o bot e ver menu principal
- `/pix [valor]` - Gerar pagamento PIX (ex: /pix 10)
- `/historico` - Ver histórico de compras
- `/afiliados` - Sistema de indicação
- `/id` - Ver seu ID
- `/saldo` - Verificar saldo atual
- `/ranking` - Ver rankings
- `/termos` - Termos de uso
- `/alertas` - Configurar alertas de estoque

#### Interface Principal:
1. **Logins | Contas Premium** - Catálogo de produtos
2. **Perfil** - Informações da conta
3. **Recarga** - Adicionar saldo via PIX
4. **Ranking** - Rankings interativos
5. **Suporte** - Contato direto
6. **Pesquisar Serviço** - Busca de produtos

### Para Administradores (Admin Bot)

#### Comandos:
- `/start` ou `/admin` - Acessar dashboard

#### Funcionalidades:
1. **Configurações**:
   - Configurações gerais do sistema
   - Gerenciar administradores
   - Configurar sistema de afiliados
   - Gerenciar usuários
   - Configurar PIX e pagamentos
   - Gerenciar catálogo de produtos

2. **Ações**:
   - Estatísticas detalhadas
   - Usuários online
   - Backup do sistema
   - Logs de atividade

3. **Transações**:
   - Recargas pendentes/aprovadas
   - Vendas recentes
   - Relatórios financeiros

4. **Atualizações**:
   - Versão atual
   - Verificar atualizações
   - Changelog

## 🛡️ Segurança

- **Criptografia**: Dados sensíveis criptografados
- **Logs de Auditoria**: Monitoramento completo de atividades
- **Detecção de Fraudes**: Sistema anti-abuse integrado
- **Controle de Acesso**: Permissões granulares
- **Rate Limiting**: Proteção contra spam

## 💰 Sistema de Pagamentos

### PIX Automático
- Geração instantânea de QR Codes
- Verificação automática de pagamentos
- Crédito imediato no saldo
- Expiração configurável (padrão: 10 minutos)

### Configurações de Depósito
- Valor mínimo: R$ 2,00
- Valor máximo: R$ 1.000,00
- Bônus configurável por depósito
- Comissões de afiliados automáticas

## 📊 Relatórios e Analytics

### Métricas Disponíveis:
- Total de usuários
- Receita total/mensal/diária
- Vendas realizadas
- Rankings dinâmicos
- Produtos mais vendidos
- Usuários mais ativos

## 🔄 Sistema de Sincronização

- **Tempo Real**: Mudanças no admin refletem instantaneamente na loja
- **Estoque Automático**: Controle automático de disponibilidade
- **Preços Dinâmicos**: Alterações de preços em tempo real
- **Notificações**: Alertas automáticos de reabastecimento

## 📂 Estrutura do Projeto

```
joazinho-store-bot/
├── config.py              # Configurações do sistema
├── database.py             # Modelos do banco de dados
├── utils.py               # Funções utilitárias
├── languages.py           # Sistema multilíngue
├── payment.py             # Sistema de pagamentos
├── store_bot.py           # Bot da loja (clientes)
├── admin_bot.py           # Bot administrativo
├── run_bots.py            # Launcher principal
├── setup.py               # Script de configuração
├── requirements.txt       # Dependências
└── README.md              # Documentação
```

## 🐛 Solução de Problemas

### Problemas Comuns:

1. **Erro de Conexão com Banco**:
   - Verifique as credenciais em `config.py`
   - Certifique-se que o MySQL está rodando

2. **Bot Não Responde**:
   - Verifique se os tokens estão corretos
   - Confirme que os bots estão ativos no BotFather

3. **Pagamentos Não Funcionam**:
   - Verifique as configurações PIX
   - Confirme os tokens de pagamento

### Logs:
Os logs do sistema são enviados para o chat configurado em `LOG_CHAT_ID`.

## 🤝 Suporte

- **Telegram**: @suporte_joaozinstore
- **Email**: suporte@joazinhostore.com
- **Horário**: 24/7

## 📄 Licença

Este projeto é proprietário. Todos os direitos reservados.

## 🔄 Atualizações

### Versão Atual: V4.1.0

### Próximas Funcionalidades:
- [ ] Sistema de cupons de desconto
- [ ] Integração com mais gateways de pagamento
- [ ] App mobile complementar
- [ ] API REST para integrações
- [ ] Sistema de reviews de produtos

## 📞 Contato

Para mais informações sobre licenciamento ou suporte técnico, entre em contato através dos canais oficiais.

---

**Joazinho Store Bot System** - Transformando vendas digitais com automação inteligente! 🚀
