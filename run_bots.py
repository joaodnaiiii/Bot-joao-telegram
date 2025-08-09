#!/usr/bin/env python3
"""
Joazinho Store Bot System
Main launcher script to run both store and admin bots
"""

import threading
import time
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def run_store_bot():
    """Run the store bot"""
    try:
        print("🏪 Starting Store Bot...")
        from store_bot import bot
        bot.polling(none_stop=True, interval=1, timeout=20)
    except Exception as e:
        print(f"❌ Store Bot error: {e}")
        time.sleep(5)
        run_store_bot()  # Restart on error

def run_admin_bot():
    """Run the admin bot"""
    try:
        print("👨‍💼 Starting Admin Bot...")
        from admin_bot import bot
        bot.polling(none_stop=True, interval=1, timeout=20)
    except Exception as e:
        print(f"❌ Admin Bot error: {e}")
        time.sleep(5)
        run_admin_bot()  # Restart on error

def main():
    """Main function to start both bots"""
    print("🚀 Joazinho Store Bot System Starting...")
    print("=" * 50)
    
    # Create database tables
    try:
        from database import create_tables
        create_tables()
        print("✅ Database tables created/verified")
    except Exception as e:
        print(f"❌ Database error: {e}")
        print("Please check your database configuration in config.py")
        return
    
    # Start both bots in separate threads
    store_thread = threading.Thread(target=run_store_bot, daemon=True)
    admin_thread = threading.Thread(target=run_admin_bot, daemon=True)
    
    store_thread.start()
    admin_thread.start()
    
    print("✅ Both bots started successfully!")
    print("Store Bot: Customer interface")
    print("Admin Bot: Management interface")
    print("=" * 50)
    print("Press Ctrl+C to stop both bots")
    
    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down bots...")
        sys.exit(0)

if __name__ == "__main__":
    main()