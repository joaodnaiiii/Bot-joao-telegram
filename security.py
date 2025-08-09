import hashlib
import hmac
import secrets
import bcrypt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import time
import jwt
from datetime import datetime, timedelta
import logging
import re
from typing import Dict, Any, Optional, List
from config import ENCRYPTION_KEY
from database import db

logger = logging.getLogger(__name__)

class SecurityManager:
    def __init__(self):
        self.cipher = Fernet(ENCRYPTION_KEY)
        self.failed_attempts = {}  # user_id: {'count': int, 'last_attempt': timestamp}
        self.max_attempts = 5
        self.lockout_duration = 300  # 5 minutos
        self.session_duration = 3600  # 1 hora
        
    def hash_password(self, password: str) -> str:
        """Gera hash seguro da senha"""
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verifica se a senha está correta"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except Exception as e:
            logger.error(f"Erro ao verificar senha: {e}")
            return False
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Criptografa dados sensíveis"""
        try:
            if isinstance(data, str):
                data = data.encode('utf-8')
            encrypted = self.cipher.encrypt(data)
            return base64.b64encode(encrypted).decode('utf-8')
        except Exception as e:
            logger.error(f"Erro ao criptografar dados: {e}")
            raise
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Descriptografa dados sensíveis"""
        try:
            decoded = base64.b64decode(encrypted_data.encode('utf-8'))
            decrypted = self.cipher.decrypt(decoded)
            return decrypted.decode('utf-8')
        except Exception as e:
            logger.error(f"Erro ao descriptografar dados: {e}")
            raise
    
    def generate_secure_token(self, length: int = 32) -> str:
        """Gera token seguro"""
        return secrets.token_urlsafe(length)
    
    def generate_session_token(self, user_id: int, admin: bool = False) -> str:
        """Gera token de sessão JWT"""
        try:
            payload = {
                'user_id': user_id,
                'admin': admin,
                'exp': datetime.utcnow() + timedelta(seconds=self.session_duration),
                'iat': datetime.utcnow(),
                'jti': secrets.token_hex(16)  # JWT ID único
            }
            
            return jwt.encode(payload, ENCRYPTION_KEY, algorithm='HS256')
        except Exception as e:
            logger.error(f"Erro ao gerar token de sessão: {e}")
            return None
    
    def validate_session_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Valida token de sessão JWT"""
        try:
            payload = jwt.decode(token, ENCRYPTION_KEY, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token de sessão expirado")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Token de sessão inválido: {e}")
            return None
    
    def check_rate_limit(self, user_id: int, action: str = 'general') -> bool:
        """Verifica limite de taxa para prevenir spam"""
        current_time = time.time()
        key = f"{user_id}_{action}"
        
        if key not in self.failed_attempts:
            self.failed_attempts[key] = {'count': 0, 'last_attempt': current_time}
            return True
        
        attempt_data = self.failed_attempts[key]
        
        # Reset contador se passou do tempo de lockout
        if current_time - attempt_data['last_attempt'] > self.lockout_duration:
            attempt_data['count'] = 0
        
        # Verificar se excedeu tentativas
        if attempt_data['count'] >= self.max_attempts:
            if current_time - attempt_data['last_attempt'] < self.lockout_duration:
                return False
            else:
                # Reset após lockout
                attempt_data['count'] = 0
        
        return True
    
    def record_failed_attempt(self, user_id: int, action: str = 'general'):
        """Registra tentativa falha"""
        current_time = time.time()
        key = f"{user_id}_{action}"
        
        if key not in self.failed_attempts:
            self.failed_attempts[key] = {'count': 1, 'last_attempt': current_time}
        else:
            self.failed_attempts[key]['count'] += 1
            self.failed_attempts[key]['last_attempt'] = current_time
        
        # Log da tentativa suspeita
        db.add_log(user_id, f"failed_attempt_{action}", f"Tentativa falha registrada")
        
        # Se excedeu limite, registrar bloqueio
        if self.failed_attempts[key]['count'] >= self.max_attempts:
            db.add_log(user_id, f"user_locked_{action}", f"Usuário bloqueado por {self.lockout_duration}s")
    
    def validate_input_data(self, data: str, data_type: str) -> bool:
        """Valida dados de entrada para prevenir injeção"""
        if not data:
            return False
        
        # Limitar tamanho
        if len(data) > 1000:
            return False
        
        # Validações específicas por tipo
        if data_type == 'email':
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            return bool(re.match(pattern, data))
        
        elif data_type == 'phone':
            pattern = r'^\+?[\d\s\-\(\)]{10,20}$'
            return bool(re.match(pattern, data))
        
        elif data_type == 'username':
            pattern = r'^[a-zA-Z0-9_]{3,30}$'
            return bool(re.match(pattern, data))
        
        elif data_type == 'amount':
            try:
                amount = float(data)
                return 0 <= amount <= 100000  # Limites razoáveis
            except:
                return False
        
        elif data_type == 'text':
            # Verificar caracteres suspeitos
            suspicious_patterns = [
                r'<script',
                r'javascript:',
                r'onload=',
                r'onerror=',
                r'SELECT.*FROM',
                r'INSERT.*INTO',
                r'DELETE.*FROM',
                r'UPDATE.*SET',
                r'DROP.*TABLE'
            ]
            
            data_lower = data.lower()
            for pattern in suspicious_patterns:
                if re.search(pattern, data_lower, re.IGNORECASE):
                    return False
            
            return True
        
        return True
    
    def sanitize_input(self, data: str) -> str:
        """Sanitiza dados de entrada"""
        if not data:
            return ""
        
        # Remover caracteres perigosos
        data = re.sub(r'[<>"\']', '', data)
        
        # Limitar tamanho
        if len(data) > 1000:
            data = data[:1000]
        
        return data.strip()
    
    def detect_suspicious_activity(self, user_id: int, action: str, details: Dict[str, Any]) -> bool:
        """Detecta atividade suspeita"""
        try:
            current_time = time.time()
            
            # Verificar múltiplas tentativas em pouco tempo
            cursor = db.connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM logs 
                WHERE user_id = %s 
                AND action = %s 
                AND created_at >= DATE_SUB(NOW(), INTERVAL 5 MINUTE)
            """, (user_id, action))
            
            recent_count = cursor.fetchone()['count']
            
            # Limites por tipo de ação
            limits = {
                'login_attempt': 10,
                'purchase_attempt': 20,
                'recharge_attempt': 15,
                'button_click': 100
            }
            
            limit = limits.get(action, 50)
            
            if recent_count > limit:
                # Registrar atividade suspeita
                db.add_log(
                    user_id, 
                    'suspicious_activity', 
                    f"Muitas tentativas de {action}: {recent_count} em 5 min"
                )
                return True
            
            # Verificar padrões suspeitos específicos
            if action == 'purchase_attempt':
                # Muitas compras do mesmo produto
                service_id = details.get('service_id')
                if service_id:
                    cursor.execute("""
                        SELECT COUNT(*) as count
                        FROM transactions 
                        WHERE user_id = %s 
                        AND service_id = %s 
                        AND created_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
                    """, (user_id, service_id))
                    
                    same_product_count = cursor.fetchone()['count']
                    if same_product_count > 5:
                        return True
            
            elif action == 'recharge_attempt':
                # Valores suspeitos de recarga
                amount = details.get('amount', 0)
                if amount > 1000 or amount < 1:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Erro ao detectar atividade suspeita: {e}")
            return False
    
    def generate_webhook_signature(self, payload: str, secret: str) -> str:
        """Gera assinatura para webhook"""
        return hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def verify_webhook_signature(self, payload: str, signature: str, secret: str) -> bool:
        """Verifica assinatura do webhook"""
        expected_signature = self.generate_webhook_signature(payload, secret)
        return hmac.compare_digest(signature, expected_signature)
    
    def mask_sensitive_data(self, data: str, data_type: str) -> str:
        """Mascara dados sensíveis para logs"""
        if not data:
            return ""
        
        if data_type == 'email':
            parts = data.split('@')
            if len(parts) == 2:
                username = parts[0]
                domain = parts[1]
                masked_username = username[0] + '*' * (len(username) - 2) + username[-1] if len(username) > 2 else '*'
                return f"{masked_username}@{domain}"
        
        elif data_type == 'phone':
            if len(data) > 4:
                return data[:2] + '*' * (len(data) - 4) + data[-2:]
        
        elif data_type == 'credit_card':
            if len(data) > 4:
                return '*' * (len(data) - 4) + data[-4:]
        
        elif data_type == 'password':
            return '*' * len(data)
        
        # Tipo genérico
        if len(data) > 6:
            return data[:2] + '*' * (len(data) - 4) + data[-2:]
        else:
            return '*' * len(data)
    
    def get_client_ip(self, update) -> str:
        """Extrai IP do cliente (quando disponível)"""
        # No Telegram, não temos acesso direto ao IP do usuário
        # Esta função é preparada para futuras integrações web
        return "telegram_user"
    
    def log_security_event(self, user_id: int, event_type: str, details: str, severity: str = 'info'):
        """Registra evento de segurança"""
        try:
            db.add_log(user_id, f"security_{event_type}", f"[{severity.upper()}] {details}")
            
            if severity in ['warning', 'error', 'critical']:
                logger.warning(f"Evento de segurança - User {user_id}: {event_type} - {details}")
        
        except Exception as e:
            logger.error(f"Erro ao registrar evento de segurança: {e}")
    
    def check_user_permissions(self, user_id: int, required_permission: str) -> bool:
        """Verifica permissões do usuário"""
        try:
            user = db.get_user(user_id)
            if not user:
                return False
            
            # Verificar se usuário está banido
            if user.get('is_banned'):
                return False
            
            # Verificar permissões específicas
            if required_permission == 'admin':
                return user.get('is_admin', False)
            
            elif required_permission == 'purchase':
                # Usuário pode comprar se não estiver banido
                return True
            
            elif required_permission == 'recharge':
                # Usuário pode recarregar se não estiver banido
                return True
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao verificar permissões: {e}")
            return False
    
    def cleanup_old_attempts(self):
        """Limpa tentativas antigas do cache"""
        current_time = time.time()
        keys_to_remove = []
        
        for key, data in self.failed_attempts.items():
            if current_time - data['last_attempt'] > self.lockout_duration * 2:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.failed_attempts[key]
    
    def get_security_report(self, days: int = 7) -> Dict[str, Any]:
        """Gera relatório de segurança"""
        try:
            cursor = db.connection.cursor(dictionary=True)
            
            # Eventos de segurança recentes
            cursor.execute("""
                SELECT action, COUNT(*) as count
                FROM logs 
                WHERE action LIKE 'security_%' 
                AND created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
                GROUP BY action
                ORDER BY count DESC
            """, (days,))
            security_events = cursor.fetchall()
            
            # Usuários com mais tentativas falhas
            cursor.execute("""
                SELECT user_id, COUNT(*) as failed_attempts
                FROM logs 
                WHERE action LIKE 'failed_attempt_%' 
                AND created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
                GROUP BY user_id
                ORDER BY failed_attempts DESC
                LIMIT 10
            """, (days,))
            top_failed_users = cursor.fetchall()
            
            # Atividades suspeitas
            cursor.execute("""
                SELECT COUNT(*) as suspicious_count
                FROM logs 
                WHERE action = 'suspicious_activity' 
                AND created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
            """, (days,))
            suspicious_count = cursor.fetchone()['suspicious_count']
            
            return {
                'period_days': days,
                'security_events': security_events,
                'top_failed_users': top_failed_users,
                'suspicious_activities': suspicious_count,
                'active_lockouts': len(self.failed_attempts),
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erro ao gerar relatório de segurança: {e}")
            return {}

# Instância global do gerenciador de segurança
security_manager = SecurityManager()

# Decorador para verificar autenticação
def require_auth(permission: str = None):
    """Decorador para verificar autenticação e permissões"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Implementar verificação de autenticação
            # Esta é uma versão simplificada
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Função para validar dados de entrada
def validate_and_sanitize(data: str, data_type: str) -> tuple[bool, str]:
    """Valida e sanitiza dados de entrada"""
    is_valid = security_manager.validate_input_data(data, data_type)
    sanitized = security_manager.sanitize_input(data) if is_valid else ""
    return is_valid, sanitized