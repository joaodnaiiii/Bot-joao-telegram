#!/usr/bin/env python3
"""
Joazinho Store Bot System Setup
Initial setup and configuration script
"""

import sys
import os
import getpass
from database import SessionLocal, User, Service, Account, create_tables
import config
import utils

def setup_database():
    """Create database tables and initial data"""
    print("📦 Setting up database...")
    try:
        create_tables()
        print("✅ Database tables created successfully!")
        return True
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

def setup_admin_user():
    """Setup initial admin user"""
    print("\n👨‍💼 Setting up admin user...")
    
    admin_id = input("Enter your Telegram user ID (admin): ")
    try:
        admin_id = int(admin_id)
        
        # Update config with admin ID
        config.ADMIN_IDS = [admin_id]
        
        # Create admin user in database
        db = SessionLocal()
        try:
            admin_user = db.query(User).filter(User.telegram_id == admin_id).first()
            if not admin_user:
                admin_user = User(
                    telegram_id=admin_id,
                    username="admin",
                    first_name="Admin",
                    is_admin=True,
                    balance=1000.0  # Give admin some initial balance for testing
                )
                db.add(admin_user)
                db.commit()
                print(f"✅ Admin user created with ID: {admin_id}")
            else:
                admin_user.is_admin = True
                db.commit()
                print(f"✅ User {admin_id} updated to admin")
        finally:
            db.close()
            
        return True
    except ValueError:
        print("❌ Invalid Telegram ID")
        return False

def setup_sample_products():
    """Setup sample products for testing"""
    print("\n🎮 Setting up sample products...")
    
    sample_products = [
        {
            "name": "ACESSO: PAINEL IPTV (10 CREDITOS)",
            "price": 20.00,
            "description": "Aviso Importante:\nInformamos que não realizamos reembolsos via Pix, apenas em créditos no bot, correspondendo aos dias restantes até o vencimento.\nAgradecemos pela compreensão e desejamos boas compras!\n\nObs: O prazo de entrega é até 24 horas.\nObs: Olhe atentamente a o texto da compra.",
            "category": "IPTV",
            "accounts": [
                {"login": "iptv_user1@example.com", "password": "senha123", "info": "Duração: 30 dias"},
                {"login": "iptv_user2@example.com", "password": "senha456", "info": "Duração: 30 dias"},
                {"login": "iptv_user3@example.com", "password": "senha789", "info": "Duração: 30 dias"},
            ]
        },
        {
            "name": "Netflix Premium",
            "price": 15.00,
            "description": "Conta Netflix Premium com acesso total a todos os filmes e séries. Qualidade 4K disponível.",
            "category": "Streaming",
            "accounts": [
                {"login": "netflix1@example.com", "password": "netflix123", "info": "Tela completa - 30 dias"},
                {"login": "netflix2@example.com", "password": "netflix456", "info": "Tela completa - 30 dias"},
                {"login": "netflix3@example.com", "password": "netflix789", "info": "Tela completa - 30 dias"},
            ]
        },
        {
            "name": "Disney+ Premium",
            "price": 12.00,
            "description": "Conta Disney+ Premium com todos os filmes, séries e conteúdo exclusivo da Disney, Marvel, Star Wars e mais.",
            "category": "Streaming",
            "accounts": [
                {"login": "disney1@example.com", "password": "disney123", "info": "Acesso completo - 30 dias"},
                {"login": "disney2@example.com", "password": "disney456", "info": "Acesso completo - 30 dias"},
            ]
        },
        {
            "name": "Amazon Prime Video",
            "price": 18.00,
            "description": "Conta Amazon Prime Video completa com filmes, séries e conteúdo original Amazon.",
            "category": "Streaming",
            "accounts": [
                {"login": "prime1@example.com", "password": "prime123", "info": "Prime completo - 30 dias"},
                {"login": "prime2@example.com", "password": "prime456", "info": "Prime completo - 30 dias"},
            ]
        }
    ]
    
    db = SessionLocal()
    try:
        added_services = 0
        added_accounts = 0
        
        for product_data in sample_products:
            # Check if service already exists
            existing_service = db.query(Service).filter(Service.name == product_data["name"]).first()
            if existing_service:
                print(f"⚠️ Service '{product_data['name']}' already exists, skipping...")
                continue
            
            # Create service
            service = Service(
                name=product_data["name"],
                description=product_data["description"],
                price=product_data["price"],
                category=product_data["category"],
                is_active=True
            )
            db.add(service)
            db.commit()
            db.refresh(service)
            added_services += 1
            
            # Add accounts
            for account_data in product_data["accounts"]:
                account = Account(
                    service_id=service.id,
                    login=account_data["login"],
                    password=utils.encrypt_data(account_data["password"]),
                    additional_info=account_data["info"],
                    is_sold=False
                )
                db.add(account)
                added_accounts += 1
            
            db.commit()
        
        print(f"✅ Added {added_services} services and {added_accounts} accounts")
        return True
        
    except Exception as e:
        print(f"❌ Error setting up products: {e}")
        return False
    finally:
        db.close()

def check_configuration():
    """Check bot configuration"""
    print("\n⚙️ Checking configuration...")
    
    issues = []
    
    # Check tokens
    if not config.STORE_BOT_TOKEN or config.STORE_BOT_TOKEN == "YOUR_STORE_BOT_TOKEN":
        issues.append("Store bot token not configured")
    
    if not config.ADMIN_BOT_TOKEN or config.ADMIN_BOT_TOKEN == "YOUR_ADMIN_BOT_TOKEN":
        issues.append("Admin bot token not configured")
    
    # Check database
    if "localhost" in config.DATABASE_URL and "password" in config.DATABASE_URL:
        issues.append("Database URL still using default values")
    
    if issues:
        print("⚠️ Configuration issues found:")
        for issue in issues:
            print(f"  - {issue}")
        print("\nPlease update config.py with your actual values")
        return False
    else:
        print("✅ Configuration looks good!")
        return True

def main():
    """Main setup function"""
    print("🚀 Joazinho Store Bot System Setup")
    print("=" * 50)
    
    # Check configuration
    if not check_configuration():
        print("\n❌ Please fix configuration issues before continuing")
        return
    
    # Setup database
    if not setup_database():
        print("\n❌ Database setup failed. Please check your database configuration.")
        return
    
    # Setup admin user
    if not setup_admin_user():
        print("\n❌ Admin setup failed")
        return
    
    # Setup sample products
    setup_sample = input("\nSetup sample products for testing? (y/n): ").lower().strip()
    if setup_sample in ['y', 'yes']:
        setup_sample_products()
    
    print("\n" + "=" * 50)
    print("✅ Setup completed successfully!")
    print("\nNext steps:")
    print("1. Update config.py with your actual values if needed")
    print("2. Run: python run_bots.py")
    print("3. Start your store bot and admin bot")
    print("\nBot Information:")
    print(f"Store Bot Token: {config.STORE_BOT_TOKEN}")
    print(f"Admin Bot Token: {config.ADMIN_BOT_TOKEN}")
    print(f"Admin IDs: {config.ADMIN_IDS}")

if __name__ == "__main__":
    main()