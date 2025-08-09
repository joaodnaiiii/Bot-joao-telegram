#!/usr/bin/env python3
"""
Script para descobrir seu Telegram ID
Execute este script e mande qualquer mensagem para o bot para descobrir seu ID
"""

import telebot
import config

# Use o token do admin bot para descobrir IDs
bot = telebot.TeleBot(config.ADMIN_BOT_TOKEN)

@bot.message_handler(func=lambda message: True)
def get_user_id(message):
    user_id = message.from_user.id
    username = message.from_user.username or "N/A"
    first_name = message.from_user.first_name or "N/A"
    
    response = f"""🆔 **INFORMAÇÕES DO USUÁRIO**

👤 Nome: {first_name}
🔗 Username: @{username}
🆔 **SEU TELEGRAM ID: {user_id}**

📝 **PARA CONFIGURAR COMO ADMIN:**
1. Abra o arquivo `config.py`
2. Encontre a linha: `ADMIN_IDS = [123456789, 987654321]`
3. Substitua por: `ADMIN_IDS = [{user_id}]`
4. Salve o arquivo
5. Reinicie os bots

✅ Depois disso você poderá usar `/admin` no bot administrativo!"""

    bot.reply_to(message, response, parse_mode='Markdown')
    print(f"User ID descoberto: {user_id} ({first_name}, @{username})")

if __name__ == "__main__":
    print("🤖 Bot para descobrir Telegram ID iniciado...")
    print("📱 Mande qualquer mensagem para o bot para descobrir seu ID")
    print("🛑 Pressione Ctrl+C para parar")
    
    try:
        bot.polling(none_stop=True)
    except KeyboardInterrupt:
        print("\n👋 Bot parado!")