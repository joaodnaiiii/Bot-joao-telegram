#!/usr/bin/env python3
"""
Joazinho Store Bot System - Test Script
Basic system functionality tests
"""

import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test if all modules can be imported"""
    print("🧪 Testing imports...")
    
    try:
        import config
        print("✅ config.py imported successfully")
    except Exception as e:
        print(f"❌ config.py import failed: {e}")
        return False
    
    try:
        import database
        print("✅ database.py imported successfully")
    except Exception as e:
        print(f"❌ database.py import failed: {e}")
        return False
    
    try:
        import utils
        print("✅ utils.py imported successfully")
    except Exception as e:
        print(f"❌ utils.py import failed: {e}")
        return False
    
    try:
        import languages
        print("✅ languages.py imported successfully")
    except Exception as e:
        print(f"❌ languages.py import failed: {e}")
        return False
    
    try:
        import payment
        print("✅ payment.py imported successfully")
    except Exception as e:
        print(f"❌ payment.py import failed: {e}")
        return False
    
    return True

def test_database_connection():
    """Test database connection"""
    print("\n🗄️ Testing database connection...")
    
    try:
        from database import SessionLocal, create_tables
        
        # Test connection
        db = SessionLocal()
        db.close()
        print("✅ Database connection successful")
        
        # Test table creation
        create_tables()
        print("✅ Database tables verified")
        
        return True
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_encryption():
    """Test encryption/decryption"""
    print("\n🔒 Testing encryption...")
    
    try:
        from utils import encrypt_data, decrypt_data
        
        test_data = "test_password_123"
        encrypted = encrypt_data(test_data)
        decrypted = decrypt_data(encrypted)
        
        if decrypted == test_data:
            print("✅ Encryption/decryption working correctly")
            return True
        else:
            print("❌ Encryption/decryption failed - data mismatch")
            return False
    except Exception as e:
        print(f"❌ Encryption test failed: {e}")
        return False

def test_pix_generation():
    """Test PIX QR code generation"""
    print("\n💳 Testing PIX generation...")
    
    try:
        from payment import PixPayment
        
        pix = PixPayment()
        result = pix.generate_qr_code(10.0, 123456)
        
        if result and 'qr_code' in result:
            print("✅ PIX QR code generation working")
            return True
        else:
            print("❌ PIX QR code generation failed")
            return False
    except Exception as e:
        print(f"❌ PIX test failed: {e}")
        return False

def test_translations():
    """Test translation system"""
    print("\n🌐 Testing translations...")
    
    try:
        from languages import get_text
        
        # Test Portuguese
        pt_text = get_text('welcome', 'pt')
        if 'Bem-vindo' in pt_text:
            print("✅ Portuguese translations working")
        else:
            print("❌ Portuguese translations failed")
            return False
        
        # Test English
        en_text = get_text('welcome', 'en')
        if 'Welcome' in en_text:
            print("✅ English translations working")
        else:
            print("❌ English translations failed")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Translation test failed: {e}")
        return False

def test_bot_tokens():
    """Test bot tokens configuration"""
    print("\n🤖 Testing bot tokens...")
    
    try:
        import config
        
        if config.STORE_BOT_TOKEN and len(config.STORE_BOT_TOKEN) > 10:
            print("✅ Store bot token configured")
        else:
            print("⚠️ Store bot token not properly configured")
        
        if config.ADMIN_BOT_TOKEN and len(config.ADMIN_BOT_TOKEN) > 10:
            print("✅ Admin bot token configured")
        else:
            print("⚠️ Admin bot token not properly configured")
        
        return True
    except Exception as e:
        print(f"❌ Bot token test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Joazinho Store Bot System - Test Suite")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_database_connection,
        test_encryption,
        test_pix_generation,
        test_translations,
        test_bot_tokens
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System is ready to use.")
        print("\nNext steps:")
        print("1. Run: python setup.py (if not done yet)")
        print("2. Run: python run_bots.py")
    else:
        print("⚠️ Some tests failed. Please check the issues above.")
        print("Make sure to:")
        print("1. Install all dependencies: pip install -r requirements.txt")
        print("2. Configure database in config.py")
        print("3. Set up proper bot tokens")

if __name__ == "__main__":
    main()