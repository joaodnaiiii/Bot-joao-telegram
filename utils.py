import hashlib
import base64
from cryptography.fernet import Fernet
from datetime import datetime, timedelta
import re
import config
from database import SessionLocal, User, Log

def encrypt_data(data):
    """Encrypt sensitive data"""
    try:
        key = config.ENCRYPTION_KEY.encode()
        if len(key) != 32:
            key = hashlib.sha256(key).digest()
        
        f = Fernet(base64.urlsafe_b64encode(key))
        encrypted_data = f.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted_data).decode()
    except Exception as e:
        print(f"Encryption error: {e}")
        return data

def decrypt_data(encrypted_data):
    """Decrypt sensitive data"""
    try:
        key = config.ENCRYPTION_KEY.encode()
        if len(key) != 32:
            key = hashlib.sha256(key).digest()
        
        f = Fernet(base64.urlsafe_b64encode(key))
        decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
        decrypted_data = f.decrypt(decoded_data)
        return decrypted_data.decode()
    except Exception as e:
        print(f"Decryption error: {e}")
        return encrypted_data

def is_admin(user_id):
    """Check if user is admin"""
    return user_id in config.ADMIN_IDS

def get_or_create_user(telegram_id, username=None, first_name=None, last_name=None):
    """Get existing user or create new one"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        
        if not user:
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                is_admin=is_admin(telegram_id)
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            
            # Log new user registration
            log_user_action(user.id, "USER_REGISTERED", f"New user registered: {username or first_name}")
        
        return user
    finally:
        db.close()

def log_user_action(user_id, action, details=None, ip_address=None):
    """Log user actions for security and analytics"""
    db = SessionLocal()
    try:
        log_entry = Log(
            user_id=user_id,
            action=action,
            details=details,
            ip_address=ip_address
        )
        db.add(log_entry)
        db.commit()
    except Exception as e:
        print(f"Logging error: {e}")
    finally:
        db.close()

def validate_amount(amount_str):
    """Validate monetary amount input"""
    try:
        amount = float(amount_str.replace(',', '.'))
        if amount < 5.0:
            return None
        return round(amount, 2)
    except (ValueError, AttributeError):
        return None

def generate_referral_code(user_id):
    """Generate unique referral code for user"""
    return hashlib.md5(f"ref_{user_id}_{config.ENCRYPTION_KEY}".encode()).hexdigest()[:8].upper()

def get_user_from_referral_code(referral_code):
    """Get user ID from referral code"""
    db = SessionLocal()
    try:
        users = db.query(User).all()
        for user in users:
            if generate_referral_code(user.id) == referral_code.upper():
                return user.id
        return None
    finally:
        db.close()

def format_currency(amount):
    """Format amount as currency"""
    return f"R$ {amount:.2f}"

def sanitize_input(text):
    """Sanitize user input to prevent injection attacks"""
    if not text:
        return ""
    
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\']', '', str(text))
    return sanitized.strip()

def rate_limit_check(user_id, action, limit=5, window_minutes=1):
    """Check if user is rate limited for specific action"""
    db = SessionLocal()
    try:
        since = datetime.utcnow() - timedelta(minutes=window_minutes)
        count = db.query(Log).filter(
            Log.user_id == user_id,
            Log.action == action,
            Log.created_at >= since
        ).count()
        
        return count < limit
    finally:
        db.close()

def is_valid_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def mask_sensitive_data(data, mask_char='*', show_chars=2):
    """Mask sensitive data for logging"""
    if not data or len(data) <= show_chars * 2:
        return mask_char * 8
    
    return data[:show_chars] + mask_char * (len(data) - show_chars * 2) + data[-show_chars:]

def get_user_stats(user_id):
    """Get user statistics"""
    from database import Purchase
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        purchases_count = db.query(Purchase).filter(Purchase.user_id == user_id).count()
        total_spent = db.query(Purchase).filter(Purchase.user_id == user_id).with_entities(
            db.func.sum(Purchase.amount)
        ).scalar() or 0
        
        referrals_count = db.query(User).filter(User.referrer_id == user_id).count()
        
        return {
            'balance': user.balance,
            'purchases_count': purchases_count,
            'total_spent': total_spent,
            'referrals_count': referrals_count,
            'member_since': user.created_at.strftime('%d/%m/%Y'),
            'referral_code': generate_referral_code(user.id)
        }
    finally:
        db.close()

def detect_suspicious_activity(user_id, action, details=None):
    """Detect suspicious user activity"""
    db = SessionLocal()
    try:
        # Check for rapid successive actions
        recent_actions = db.query(Log).filter(
            Log.user_id == user_id,
            Log.created_at >= datetime.utcnow() - timedelta(minutes=1)
        ).count()
        
        if recent_actions > 10:  # More than 10 actions per minute
            log_user_action(user_id, "SUSPICIOUS_ACTIVITY", f"Rapid actions detected: {recent_actions}/min")
            return True
        
        # Check for unusual patterns
        if action == "PURCHASE_ATTEMPT" and details:
            # Check for multiple failed purchases
            failed_purchases = db.query(Log).filter(
                Log.user_id == user_id,
                Log.action == "PURCHASE_FAILED",
                Log.created_at >= datetime.utcnow() - timedelta(hours=1)
            ).count()
            
            if failed_purchases > 5:
                log_user_action(user_id, "SUSPICIOUS_ACTIVITY", f"Multiple failed purchases: {failed_purchases}")
                return True
        
        return False
    finally:
        db.close()

class SecurityManager:
    """Centralized security management"""
    
    @staticmethod
    def validate_user_access(user_id, required_permission=None):
        """Validate user access and permissions"""
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                return False
            
            if required_permission == "admin" and not user.is_admin:
                return False
            
            return True
        finally:
            db.close()
    
    @staticmethod
    def block_user(user_id, reason):
        """Block user (implementation depends on your needs)"""
        log_user_action(user_id, "USER_BLOCKED", reason)
        # Additional blocking logic can be added here
    
    @staticmethod
    def audit_log(action, user_id=None, details=None):
        """Create audit log entry"""
        log_user_action(user_id, f"AUDIT_{action}", details)