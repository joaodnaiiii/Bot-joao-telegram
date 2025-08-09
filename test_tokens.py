#!/usr/bin/env python3
"""
Script para testar se os tokens dos bots estão funcionando
"""

import telebot
import config
import sys

def test_store_bot():
    """Testar bot da loja"""
    print("🏪 Testando Bot da Loja...")
    print(f"Token: {config.STORE_BOT_TOKEN[:20]}...")
    
    try:
        bot = telebot.TeleBot(config.STORE_BOT_TOKEN)
        me = bot.get_me()
        print(f"✅ Bot da Loja OK: @{me.username}")
        print(f"   Nome: {me.first_name}")
        print(f"   ID: {me.id}")
        return True
    except Exception as e:
        print(f"❌ Erro no Bot da Loja: {e}")
        return False

def test_admin_bot():
    """Testar bot admin"""
    print("\n👨‍💼 Testando Bot Admin...")
    print(f"Token: {config.ADMIN_BOT_TOKEN[:20]}...")
    
    try:
        bot = telebot.TeleBot(config.ADMIN_BOT_TOKEN)
        me = bot.get_me()
        print(f"✅ Bot Admin OK: @{me.username}")
        print(f"   Nome: {me.first_name}")
        print(f"   ID: {me.id}")
        return True
    except Exception as e:
        print(f"❌ Erro no Bot Admin: {e}")
        return False

def main():
    print("🧪 TESTANDO TOKENS DOS BOTS")
    print("=" * 40)
    
    store_ok = test_store_bot()
    admin_ok = test_admin_bot()
    
    print("\n" + "=" * 40)
    print("📊 RESULTADO DOS TESTES:")
    
    if store_ok and admin_ok:
        print("✅ TODOS OS BOTS FUNCIONANDO!")
        print(f"🆔 Seu ID configurado: {config.ADMIN_IDS[0]}")
        print("\n🚀 Você pode iniciar os bots com:")
        print("   python run_bots.py")
    else:
        print("❌ ALGUNS BOTS COM PROBLEMA!")
        print("\n🔧 POSSÍVEIS SOLUÇÕES:")
        print("1. Verifique se os tokens estão corretos")
        print("2. Verifique sua conexão com internet")
        print("3. Verifique se os bots não foram revogados no @BotFather")
        
        if not store_ok:
            print(f"\n🏪 Token da Loja: {config.STORE_BOT_TOKEN}")
        if not admin_ok:
            print(f"\n👨‍💼 Token Admin: {config.ADMIN_BOT_TOKEN}")
    
    return store_ok and admin_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)