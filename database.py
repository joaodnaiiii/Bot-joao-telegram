import mysql.connector
import os
from dotenv import load_dotenv
import hashlib
import json
from datetime import datetime
import logging

load_dotenv()

class Database:
    def __init__(self):
        self.host = os.getenv('DB_HOST')
        self.user = os.getenv('DB_USER')
        self.password = os.getenv('DB_PASSWORD')
        self.database = os.getenv('DB_NAME')
        self.connection = None
        self.connect()
        self.create_tables()

    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                charset='utf8mb4',
                autocommit=True
            )
            logging.info("✅ Conectado ao banco de dados MySQL")
        except mysql.connector.Error as err:
            logging.error(f"❌ Erro ao conectar ao banco de dados: {err}")
            # Criar banco se não existir
            try:
                temp_conn = mysql.connector.connect(
                    host=self.host,
                    user=self.user,
                    password=self.password,
                    charset='utf8mb4'
                )
                cursor = temp_conn.cursor()
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
                temp_conn.close()
                self.connection = mysql.connector.connect(
                    host=self.host,
                    user=self.user,
                    password=self.password,
                    database=self.database,
                    charset='utf8mb4',
                    autocommit=True
                )
                logging.info("✅ Banco de dados criado e conectado")
            except Exception as e:
                logging.error(f"❌ Erro crítico no banco: {e}")

    def create_tables(self):
        cursor = self.connection.cursor()
        
        # Tabela de usuários
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id BIGINT PRIMARY KEY,
                username VARCHAR(255),
                first_name VARCHAR(255),
                balance DECIMAL(10,2) DEFAULT 0.00,
                referral_code VARCHAR(50) UNIQUE,
                referred_by BIGINT,
                total_spent DECIMAL(10,2) DEFAULT 0.00,
                total_earned DECIMAL(10,2) DEFAULT 0.00,
                language VARCHAR(5) DEFAULT 'pt',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_blocked BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (referred_by) REFERENCES users(id)
            )
        ''')
        
        # Tabela de administradores
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                user_id BIGINT PRIMARY KEY,
                username VARCHAR(255),
                permissions JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Tabela de categorias
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                emoji VARCHAR(10),
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela de serviços/produtos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS services (
                id INT AUTO_INCREMENT PRIMARY KEY,
                category_id INT,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                price DECIMAL(10,2) NOT NULL,
                stock INT DEFAULT 0,
                emoji VARCHAR(10),
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories(id)
            )
        ''')
        
        # Tabela de contas/logins
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                id INT AUTO_INCREMENT PRIMARY KEY,
                service_id INT,
                email VARCHAR(255),
                password VARCHAR(255),
                additional_info TEXT,
                is_sold BOOLEAN DEFAULT FALSE,
                sold_to BIGINT,
                sold_at TIMESTAMP NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (service_id) REFERENCES services(id),
                FOREIGN KEY (sold_to) REFERENCES users(id)
            )
        ''')
        
        # Tabela de transações
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id BIGINT,
                type ENUM('purchase', 'recharge', 'commission') NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                service_id INT NULL,
                payment_method VARCHAR(50),
                payment_id VARCHAR(255),
                status ENUM('pending', 'completed', 'failed', 'cancelled') DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (service_id) REFERENCES services(id)
            )
        ''')
        
        # Tabela de pagamentos PIX
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pix_payments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                transaction_id INT,
                user_id BIGINT,
                amount DECIMAL(10,2) NOT NULL,
                qr_code TEXT,
                qr_code_base64 TEXT,
                payment_id VARCHAR(255) UNIQUE,
                status ENUM('pending', 'approved', 'rejected', 'expired') DEFAULT 'pending',
                expires_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (transaction_id) REFERENCES transactions(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Tabela de logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id BIGINT,
                action VARCHAR(255),
                details TEXT,
                ip_address VARCHAR(45),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Tabela de configurações
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key_name VARCHAR(255) PRIMARY KEY,
                value TEXT,
                description TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.close()
        logging.info("✅ Tabelas do banco de dados criadas/verificadas")

    def execute_query(self, query, params=None):
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params or ())
            result = cursor.fetchall()
            cursor.close()
            return result
        except Exception as e:
            logging.error(f"❌ Erro na query: {e}")
            return None

    def execute_insert(self, query, params=None):
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params or ())
            insert_id = cursor.lastrowid
            cursor.close()
            return insert_id
        except Exception as e:
            logging.error(f"❌ Erro no insert: {e}")
            return None

    # Métodos para usuários
    def create_user(self, user_id, username=None, first_name=None, referred_by=None):
        referral_code = hashlib.md5(str(user_id).encode()).hexdigest()[:8].upper()
        query = '''
            INSERT INTO users (id, username, first_name, referral_code, referred_by)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            username = VALUES(username),
            first_name = VALUES(first_name)
        '''
        return self.execute_insert(query, (user_id, username, first_name, referral_code, referred_by))

    def get_user(self, user_id):
        query = "SELECT * FROM users WHERE id = %s"
        result = self.execute_query(query, (user_id,))
        return result[0] if result else None

    def update_user_balance(self, user_id, amount, operation='add'):
        if operation == 'add':
            query = "UPDATE users SET balance = balance + %s WHERE id = %s"
        else:
            query = "UPDATE users SET balance = balance - %s WHERE id = %s"
        cursor = self.connection.cursor()
        cursor.execute(query, (amount, user_id))
        cursor.close()

    def get_user_by_referral(self, referral_code):
        query = "SELECT * FROM users WHERE referral_code = %s"
        result = self.execute_query(query, (referral_code,))
        return result[0] if result else None

    # Métodos para serviços
    def create_service(self, category_id, name, description, price, emoji='🛍️'):
        query = '''
            INSERT INTO services (category_id, name, description, price, emoji)
            VALUES (%s, %s, %s, %s, %s)
        '''
        return self.execute_insert(query, (category_id, name, description, price, emoji))

    def get_services(self, category_id=None, active_only=True):
        if category_id:
            query = "SELECT * FROM services WHERE category_id = %s"
            params = (category_id,)
        else:
            query = "SELECT * FROM services"
            params = ()
        
        if active_only:
            query += " AND is_active = TRUE" if "WHERE" in query else " WHERE is_active = TRUE"
        
        return self.execute_query(query, params)

    def get_service(self, service_id):
        query = "SELECT * FROM services WHERE id = %s"
        result = self.execute_query(query, (service_id,))
        return result[0] if result else None

    def update_service_stock(self, service_id):
        query = '''
            UPDATE services 
            SET stock = (
                SELECT COUNT(*) 
                FROM accounts 
                WHERE service_id = %s AND is_sold = FALSE
            ) 
            WHERE id = %s
        '''
        cursor = self.connection.cursor()
        cursor.execute(query, (service_id, service_id))
        cursor.close()

    # Métodos para categorias
    def create_category(self, name, description=None, emoji='📂'):
        query = '''
            INSERT INTO categories (name, description, emoji)
            VALUES (%s, %s, %s)
        '''
        return self.execute_insert(query, (name, description, emoji))

    def get_categories(self, active_only=True):
        query = "SELECT * FROM categories"
        if active_only:
            query += " WHERE is_active = TRUE"
        return self.execute_query(query)

    # Métodos para contas
    def add_account(self, service_id, email, password, additional_info=None):
        query = '''
            INSERT INTO accounts (service_id, email, password, additional_info)
            VALUES (%s, %s, %s, %s)
        '''
        result = self.execute_insert(query, (service_id, email, password, additional_info))
        if result:
            self.update_service_stock(service_id)
        return result

    def get_available_account(self, service_id):
        query = '''
            SELECT * FROM accounts 
            WHERE service_id = %s AND is_sold = FALSE 
            ORDER BY created_at ASC 
            LIMIT 1
        '''
        result = self.execute_query(query, (service_id,))
        return result[0] if result else None

    def sell_account(self, account_id, user_id):
        query = '''
            UPDATE accounts 
            SET is_sold = TRUE, sold_to = %s, sold_at = NOW()
            WHERE id = %s
        '''
        cursor = self.connection.cursor()
        cursor.execute(query, (user_id, account_id))
        cursor.close()

    # Métodos para transações
    def create_transaction(self, user_id, type, amount, service_id=None, payment_method='pix'):
        query = '''
            INSERT INTO transactions (user_id, type, amount, service_id, payment_method)
            VALUES (%s, %s, %s, %s, %s)
        '''
        return self.execute_insert(query, (user_id, type, amount, service_id, payment_method))

    def update_transaction_status(self, transaction_id, status, payment_id=None):
        query = "UPDATE transactions SET status = %s"
        params = [status]
        
        if payment_id:
            query += ", payment_id = %s"
            params.append(payment_id)
        
        query += " WHERE id = %s"
        params.append(transaction_id)
        
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        cursor.close()

    def get_user_transactions(self, user_id, limit=10):
        query = '''
            SELECT t.*, s.name as service_name 
            FROM transactions t
            LEFT JOIN services s ON t.service_id = s.id
            WHERE t.user_id = %s 
            ORDER BY t.created_at DESC 
            LIMIT %s
        '''
        return self.execute_query(query, (user_id, limit))

    # Métodos para PIX
    def create_pix_payment(self, transaction_id, user_id, amount, qr_code, qr_code_base64, payment_id):
        query = '''
            INSERT INTO pix_payments (transaction_id, user_id, amount, qr_code, qr_code_base64, payment_id, expires_at)
            VALUES (%s, %s, %s, %s, %s, %s, DATE_ADD(NOW(), INTERVAL 30 MINUTE))
        '''
        return self.execute_insert(query, (transaction_id, user_id, amount, qr_code, qr_code_base64, payment_id))

    def get_pix_payment(self, payment_id):
        query = "SELECT * FROM pix_payments WHERE payment_id = %s"
        result = self.execute_query(query, (payment_id,))
        return result[0] if result else None

    def update_pix_status(self, payment_id, status):
        query = "UPDATE pix_payments SET status = %s WHERE payment_id = %s"
        cursor = self.connection.cursor()
        cursor.execute(query, (status, payment_id))
        cursor.close()

    # Métodos para administradores
    def add_admin(self, user_id, username=None, permissions=None):
        if permissions is None:
            permissions = {
                "manage_services": True,
                "manage_users": True,
                "view_reports": True,
                "manage_payments": True
            }
        
        query = '''
            INSERT INTO admins (user_id, username, permissions)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
            username = VALUES(username),
            permissions = VALUES(permissions)
        '''
        return self.execute_insert(query, (user_id, username, json.dumps(permissions)))

    def is_admin(self, user_id):
        query = "SELECT * FROM admins WHERE user_id = %s"
        result = self.execute_query(query, (user_id,))
        return result[0] if result else None

    # Métodos para logs
    def add_log(self, user_id, action, details=None):
        query = '''
            INSERT INTO logs (user_id, action, details)
            VALUES (%s, %s, %s)
        '''
        self.execute_insert(query, (user_id, action, details))

    # Métodos para configurações
    def get_setting(self, key):
        query = "SELECT value FROM settings WHERE key_name = %s"
        result = self.execute_query(query, (key,))
        return result[0][0] if result else None

    def set_setting(self, key, value, description=None):
        query = '''
            INSERT INTO settings (key_name, value, description)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
            value = VALUES(value),
            description = VALUES(description),
            updated_at = NOW()
        '''
        return self.execute_insert(query, (key, value, description))

    def close(self):
        if self.connection:
            self.connection.close()

# Instância global do banco de dados
db = Database()