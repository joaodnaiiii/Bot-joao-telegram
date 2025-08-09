import mysql.connector
from mysql.connector import Error
import bcrypt
from datetime import datetime, timedelta
import json
from config import DB_CONFIG, ENCRYPTION_KEY
from cryptography.fernet import Fernet
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.connection = None
        self.cipher = Fernet(ENCRYPTION_KEY)
        
    def connect(self):
        """Conecta ao banco de dados MySQL"""
        try:
            self.connection = mysql.connector.connect(**DB_CONFIG)
            if self.connection.is_connected():
                logger.info("Conexão com banco de dados estabelecida")
                return True
        except Error as e:
            logger.error(f"Erro ao conectar com banco de dados: {e}")
            return False
    
    def disconnect(self):
        """Desconecta do banco de dados"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("Conexão com banco de dados fechada")
    
    def create_tables(self):
        """Cria todas as tabelas necessárias"""
        try:
            cursor = self.connection.cursor()
            
            # Tabela de usuários
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    username VARCHAR(255),
                    first_name VARCHAR(255),
                    last_name VARCHAR(255),
                    phone VARCHAR(20),
                    balance DECIMAL(10,2) DEFAULT 0.00,
                    language VARCHAR(5) DEFAULT 'pt',
                    referrer_id BIGINT,
                    is_admin BOOLEAN DEFAULT FALSE,
                    is_banned BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_referrer (referrer_id),
                    FOREIGN KEY (referrer_id) REFERENCES users(user_id) ON DELETE SET NULL
                )
            """)
            
            # Tabela de categorias
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    emoji VARCHAR(10),
                    description TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabela de serviços
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS services (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    category_id INT,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    price DECIMAL(10,2) NOT NULL,
                    stock INT DEFAULT 0,
                    is_active BOOLEAN DEFAULT TRUE,
                    warranty_days INT DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_category (category_id),
                    INDEX idx_active (is_active),
                    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
                )
            """)
            
            # Tabela de logins/contas
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS accounts (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    service_id INT NOT NULL,
                    login_data TEXT NOT NULL,
                    is_sold BOOLEAN DEFAULT FALSE,
                    sold_to_user_id BIGINT,
                    sold_at TIMESTAMP NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_service (service_id),
                    INDEX idx_sold (is_sold),
                    FOREIGN KEY (service_id) REFERENCES services(id) ON DELETE CASCADE,
                    FOREIGN KEY (sold_to_user_id) REFERENCES users(user_id) ON DELETE SET NULL
                )
            """)
            
            # Tabela de transações
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    type ENUM('purchase', 'recharge', 'commission', 'refund') NOT NULL,
                    amount DECIMAL(10,2) NOT NULL,
                    description TEXT,
                    service_id INT,
                    account_id INT,
                    payment_id VARCHAR(255),
                    payment_status ENUM('pending', 'approved', 'rejected', 'cancelled') DEFAULT 'pending',
                    pix_qr_code TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_user (user_id),
                    INDEX idx_type (type),
                    INDEX idx_status (payment_status),
                    INDEX idx_payment (payment_id),
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                    FOREIGN KEY (service_id) REFERENCES services(id) ON DELETE SET NULL,
                    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE SET NULL
                )
            """)
            
            # Tabela de comissões
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS commissions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    referrer_id BIGINT NOT NULL,
                    referred_id BIGINT NOT NULL,
                    transaction_id INT NOT NULL,
                    amount DECIMAL(10,2) NOT NULL,
                    is_paid BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_referrer (referrer_id),
                    INDEX idx_referred (referred_id),
                    INDEX idx_paid (is_paid),
                    FOREIGN KEY (referrer_id) REFERENCES users(user_id) ON DELETE CASCADE,
                    FOREIGN KEY (referred_id) REFERENCES users(user_id) ON DELETE CASCADE,
                    FOREIGN KEY (transaction_id) REFERENCES transactions(id) ON DELETE CASCADE
                )
            """)
            
            # Tabela de logs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id BIGINT,
                    action VARCHAR(255) NOT NULL,
                    details TEXT,
                    ip_address VARCHAR(45),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_user (user_id),
                    INDEX idx_action (action),
                    INDEX idx_date (created_at),
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
                )
            """)
            
            # Tabela de configurações
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    key_name VARCHAR(255) UNIQUE NOT NULL,
                    value TEXT,
                    description TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """)
            
            self.connection.commit()
            logger.info("Tabelas criadas com sucesso")
            
            # Inserir categorias padrão
            self._insert_default_categories()
            
        except Error as e:
            logger.error(f"Erro ao criar tabelas: {e}")
            self.connection.rollback()
    
    def _insert_default_categories(self):
        """Insere categorias padrão no banco"""
        try:
            cursor = self.connection.cursor()
            default_categories = [
                ('Streaming', '📺', 'Serviços de streaming de vídeo'),
                ('Jogos', '🎮', 'Contas e serviços de jogos'),
                ('Música', '🎵', 'Serviços de streaming de música'),
                ('VPN', '🔒', 'Serviços de VPN e privacidade'),
                ('Educação', '📚', 'Plataformas educacionais'),
                ('Software', '💻', 'Licenças de software'),
                ('Outros', '🔧', 'Outros serviços')
            ]
            
            for name, emoji, description in default_categories:
                cursor.execute("""
                    INSERT IGNORE INTO categories (name, emoji, description) 
                    VALUES (%s, %s, %s)
                """, (name, emoji, description))
            
            self.connection.commit()
            logger.info("Categorias padrão inseridas")
            
        except Error as e:
            logger.error(f"Erro ao inserir categorias padrão: {e}")
    
    def encrypt_data(self, data):
        """Criptografa dados sensíveis"""
        if isinstance(data, str):
            data = data.encode()
        return self.cipher.encrypt(data).decode()
    
    def decrypt_data(self, encrypted_data):
        """Descriptografa dados"""
        if isinstance(encrypted_data, str):
            encrypted_data = encrypted_data.encode()
        return self.cipher.decrypt(encrypted_data).decode()
    
    # Métodos para usuários
    def create_user(self, user_id, username=None, first_name=None, last_name=None, referrer_id=None):
        """Cria um novo usuário"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT IGNORE INTO users (user_id, username, first_name, last_name, referrer_id) 
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, username, first_name, last_name, referrer_id))
            self.connection.commit()
            return True
        except Error as e:
            logger.error(f"Erro ao criar usuário: {e}")
            return False
    
    def get_user(self, user_id):
        """Busca informações de um usuário"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
            return cursor.fetchone()
        except Error as e:
            logger.error(f"Erro ao buscar usuário: {e}")
            return None
    
    def update_user_balance(self, user_id, amount, operation='add'):
        """Atualiza o saldo do usuário"""
        try:
            cursor = self.connection.cursor()
            if operation == 'add':
                cursor.execute("UPDATE users SET balance = balance + %s WHERE user_id = %s", (amount, user_id))
            elif operation == 'subtract':
                cursor.execute("UPDATE users SET balance = balance - %s WHERE user_id = %s", (amount, user_id))
            else:
                cursor.execute("UPDATE users SET balance = %s WHERE user_id = %s", (amount, user_id))
            
            self.connection.commit()
            return True
        except Error as e:
            logger.error(f"Erro ao atualizar saldo: {e}")
            return False
    
    # Métodos para serviços
    def get_categories(self, active_only=True):
        """Busca todas as categorias"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = "SELECT * FROM categories"
            if active_only:
                query += " WHERE is_active = TRUE"
            query += " ORDER BY name"
            cursor.execute(query)
            return cursor.fetchall()
        except Error as e:
            logger.error(f"Erro ao buscar categorias: {e}")
            return []
    
    def get_services_by_category(self, category_id, active_only=True):
        """Busca serviços por categoria"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
                SELECT s.*, c.name as category_name, c.emoji as category_emoji,
                       (SELECT COUNT(*) FROM accounts a WHERE a.service_id = s.id AND a.is_sold = FALSE) as available_stock
                FROM services s
                LEFT JOIN categories c ON s.category_id = c.id
                WHERE s.category_id = %s
            """
            params = [category_id]
            
            if active_only:
                query += " AND s.is_active = TRUE"
            
            query += " ORDER BY s.name"
            cursor.execute(query, params)
            return cursor.fetchall()
        except Error as e:
            logger.error(f"Erro ao buscar serviços: {e}")
            return []
    
    def get_service(self, service_id):
        """Busca um serviço específico"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT s.*, c.name as category_name, c.emoji as category_emoji,
                       (SELECT COUNT(*) FROM accounts a WHERE a.service_id = s.id AND a.is_sold = FALSE) as available_stock
                FROM services s
                LEFT JOIN categories c ON s.category_id = c.id
                WHERE s.id = %s
            """, (service_id,))
            return cursor.fetchone()
        except Error as e:
            logger.error(f"Erro ao buscar serviço: {e}")
            return None
    
    def add_service(self, category_id, name, description, price, stock=0, warranty_days=0):
        """Adiciona um novo serviço"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO services (category_id, name, description, price, stock, warranty_days) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (category_id, name, description, price, stock, warranty_days))
            self.connection.commit()
            return cursor.lastrowid
        except Error as e:
            logger.error(f"Erro ao adicionar serviço: {e}")
            return None
    
    def update_service(self, service_id, **kwargs):
        """Atualiza um serviço"""
        try:
            cursor = self.connection.cursor()
            fields = []
            values = []
            
            for key, value in kwargs.items():
                if key in ['category_id', 'name', 'description', 'price', 'stock', 'is_active', 'warranty_days']:
                    fields.append(f"{key} = %s")
                    values.append(value)
            
            if not fields:
                return False
            
            values.append(service_id)
            query = f"UPDATE services SET {', '.join(fields)} WHERE id = %s"
            cursor.execute(query, values)
            self.connection.commit()
            return True
        except Error as e:
            logger.error(f"Erro ao atualizar serviço: {e}")
            return False
    
    # Métodos para contas/logins
    def add_account(self, service_id, login_data):
        """Adiciona uma conta/login ao estoque"""
        try:
            cursor = self.connection.cursor()
            encrypted_data = self.encrypt_data(login_data)
            cursor.execute("""
                INSERT INTO accounts (service_id, login_data) 
                VALUES (%s, %s)
            """, (service_id, encrypted_data))
            self.connection.commit()
            return cursor.lastrowid
        except Error as e:
            logger.error(f"Erro ao adicionar conta: {e}")
            return None
    
    def get_available_account(self, service_id):
        """Busca uma conta disponível para venda"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT * FROM accounts 
                WHERE service_id = %s AND is_sold = FALSE 
                ORDER BY created_at ASC 
                LIMIT 1
            """, (service_id,))
            account = cursor.fetchone()
            
            if account:
                account['login_data'] = self.decrypt_data(account['login_data'])
            
            return account
        except Error as e:
            logger.error(f"Erro ao buscar conta disponível: {e}")
            return None
    
    def mark_account_sold(self, account_id, user_id):
        """Marca uma conta como vendida"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                UPDATE accounts 
                SET is_sold = TRUE, sold_to_user_id = %s, sold_at = CURRENT_TIMESTAMP 
                WHERE id = %s
            """, (user_id, account_id))
            self.connection.commit()
            return True
        except Error as e:
            logger.error(f"Erro ao marcar conta como vendida: {e}")
            return False
    
    # Métodos para transações
    def create_transaction(self, user_id, transaction_type, amount, description=None, service_id=None, account_id=None, payment_id=None):
        """Cria uma nova transação"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO transactions (user_id, type, amount, description, service_id, account_id, payment_id) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (user_id, transaction_type, amount, description, service_id, account_id, payment_id))
            self.connection.commit()
            return cursor.lastrowid
        except Error as e:
            logger.error(f"Erro ao criar transação: {e}")
            return None
    
    def update_transaction_status(self, transaction_id, status):
        """Atualiza o status de uma transação"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("UPDATE transactions SET payment_status = %s WHERE id = %s", (status, transaction_id))
            self.connection.commit()
            return True
        except Error as e:
            logger.error(f"Erro ao atualizar status da transação: {e}")
            return False
    
    def get_user_transactions(self, user_id, limit=20):
        """Busca transações do usuário"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT t.*, s.name as service_name 
                FROM transactions t
                LEFT JOIN services s ON t.service_id = s.id
                WHERE t.user_id = %s 
                ORDER BY t.created_at DESC 
                LIMIT %s
            """, (user_id, limit))
            return cursor.fetchall()
        except Error as e:
            logger.error(f"Erro ao buscar transações: {e}")
            return []
    
    # Métodos para logs
    def add_log(self, user_id, action, details=None, ip_address=None):
        """Adiciona um log de atividade"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO logs (user_id, action, details, ip_address) 
                VALUES (%s, %s, %s, %s)
            """, (user_id, action, details, ip_address))
            self.connection.commit()
            return True
        except Error as e:
            logger.error(f"Erro ao adicionar log: {e}")
            return False
    
    # Métodos para estatísticas
    def get_sales_stats(self, days=30):
        """Busca estatísticas de vendas"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_sales,
                    SUM(amount) as total_revenue,
                    AVG(amount) as avg_sale_value
                FROM transactions 
                WHERE type = 'purchase' 
                AND payment_status = 'approved' 
                AND created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
            """, (days,))
            return cursor.fetchone()
        except Error as e:
            logger.error(f"Erro ao buscar estatísticas: {e}")
            return None

# Instância global do banco
db = Database()