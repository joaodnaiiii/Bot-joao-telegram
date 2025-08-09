# 🚀 INSTRUÇÕES RÁPIDAS - Joazinho Store Bot

## ⚡ CONFIGURAÇÃO RÁPIDA

### 1. 🆔 Descobrir seu Telegram ID
```bash
python get_telegram_id.py
```
- Mande qualquer mensagem para o bot
- Anote seu **Telegram ID** que aparecerá

### 2. ⚙️ Configurar Admin
Abra `config.py` e substitua:
```python
ADMIN_IDS = [123456789, 987654321]  # ❌ Exemplo
```
Por:
```python
ADMIN_IDS = [SEU_TELEGRAM_ID_AQUI]  # ✅ Seu ID
```

### 3. 🗄️ Configurar Banco (Opcional)
Se quiser usar MySQL, edite em `config.py`:
```python
DATABASE_URL = 'mysql+mysqlconnector://usuario:senha@localhost/joazinho_store'
```

### 4. 🚀 Iniciar Sistema
```bash
# Instalar dependências
pip install -r requirements.txt

# Configurar sistema (primeira vez)
python setup.py

# Iniciar ambos os bots
python run_bots.py
```

## 📱 COMO USAR

### 🏪 **Bot da Loja** (Clientes)
**Token**: `8322262425:AAH3k6l9X6u1M4_FHNzG5HHLmELnfO6xqkM`

- `/start` - Menu principal com botões inline
- Botões funcionam dentro da mensagem (não embaixo)
- Interface exata como solicitado

### 👨‍💼 **Bot Admin** (Gerenciamento)  
**Token**: `7405988960:AAEQWzK9-GMiRDSGGc_yLvAq3KMYvkL6DI0`

- `/admin` - Painel administrativo completo
- Todos os botões funcionais
- Controla a loja em tempo real

## ✅ FUNCIONALIDADES PRONTAS

### ✅ Bot da Loja:
- [x] Menu com botões inline na mensagem
- [x] Layout exato: Logins comprido, Perfil+Recarga lado a lado, etc.
- [x] Ranking com 4 tipos e indicador verde
- [x] Sistema PIX com QR code
- [x] Perfil com estatísticas
- [x] Histórico de compras
- [x] Sistema de afiliados
- [x] Todos os comandos funcionando

### ✅ Bot Admin:
- [x] Dashboard completo com métricas
- [x] Configurações gerais
- [x] Gerenciar admins
- [x] Configurar afiliados
- [x] Gerenciar usuários
- [x] Configurar PIX
- [x] Gerenciar logins/estoque
- [x] Sincronização em tempo real

## 🐛 SOLUCIONANDO PROBLEMAS

### ❌ "Admin não funciona"
1. Execute: `python get_telegram_id.py`
2. Configure seu ID em `config.py`
3. Reinicie os bots

### ❌ "Botões aparecem embaixo"
✅ **CORRIGIDO!** Agora os botões aparecem como inline na mensagem

### ❌ "Erro de banco de dados"
```bash
# Use SQLite (mais simples)
# Em config.py:
DATABASE_URL = 'sqlite:///joazinho_store.db'
```

## 🎯 TESTE RÁPIDO

1. **Descobrir ID**: `python get_telegram_id.py`
2. **Configurar admin** em `config.py`
3. **Testar sistema**: `python test_system.py`
4. **Iniciar bots**: `python run_bots.py`

## 📞 TOKENS CONFIGURADOS

- **Store Bot**: `8322262425:AAH3k6l9X6u1M4_FHNzG5HHLmELnfO6xqkM`
- **Admin Bot**: `7405988960:AAEQWzK9-GMiRDSGGc_yLvAq3KMYvkL6DI0`

## 🎉 PRONTO PARA USAR!

Todos os recursos solicitados estão implementados e funcionando:
- ✅ Interface exata com botões inline
- ✅ Admin bot totalmente funcional  
- ✅ Sincronização em tempo real
- ✅ PIX automático
- ✅ Rankings dinâmicos
- ✅ Sistema completo de vendas

**Problema dos botões embaixo = RESOLVIDO!** 🎯