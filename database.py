import sqlite3
import json
from datetime import datetime, timedelta
import uuid

class Database:
    def __init__(self, db_name="joaozinho_store.db"):
        self.db_name = db_name
        self.init_database()
    
    def init_database(self):
        """Inicializa o banco de dados com todas as tabelas necessárias"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Tabela de usuários
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                name TEXT,
                phone TEXT,
                balance REAL DEFAULT 0.0,
                bonus REAL DEFAULT 0.0,
                registration_date TEXT,
                role TEXT DEFAULT "cliente"
            )
        ''')
        
        # Tabela de transações PIX
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pix_transactions (
                transaction_id TEXT PRIMARY KEY,
                user_id TEXT,
                amount REAL,
                status TEXT DEFAULT "pending",
                qr_code TEXT,
                pix_key TEXT,
                expiry_date TEXT,
                created_at TEXT,
                paid_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Tabela de produtos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                product_id TEXT PRIMARY KEY,
                name TEXT,
                price REAL,
                description TEXT,
                stock INTEGER,
                category TEXT DEFAULT "premium",
                active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Tabela de compras
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS purchases (
                purchase_id TEXT PRIMARY KEY,
                user_id TEXT,
                product_id TEXT,
                amount REAL,
                purchase_date TEXT,
                status TEXT DEFAULT "completed",
                product_data TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (product_id) REFERENCES products (product_id)
            )
        ''')
        
        # Tabela de controle de flood
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS flood_control (
                user_id TEXT PRIMARY KEY,
                last_message_time TEXT,
                flood_count INTEGER DEFAULT 0,
                blocked_until TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # Inserir produtos padrão
        self.insert_default_products()
    
    def insert_default_products(self):
        """Insere produtos padrão se não existirem"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        default_products = [
            ("netflix_premium", "Netflix Premium 1 Mês", 15.90, "Acesso completo ao Netflix Premium por 1 mês", 100),
            ("spotify_premium", "Spotify Premium 3 Meses", 25.50, "Spotify Premium sem anúncios por 3 meses", 50),
            ("disney_plus", "Disney+ Premium 6 Meses", 35.00, "Disney+ com todos os filmes e séries por 6 meses", 30),
            ("amazon_prime", "Amazon Prime 1 Ano", 89.90, "Amazon Prime Video + frete grátis por 1 ano", 20)
        ]
        
        for product_id, name, price, description, stock in default_products:
            cursor.execute('''
                INSERT OR IGNORE INTO products (product_id, name, price, description, stock)
                VALUES (?, ?, ?, ?, ?)
            ''', (product_id, name, price, description, stock))
        
        conn.commit()
        conn.close()
    
    def get_or_create_user(self, user_id, name="", phone=""):
        """Obtém ou cria um usuário"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()
        
        if not user:
            cursor.execute('''
                INSERT INTO users (user_id, name, phone, registration_date)
                VALUES (?, ?, ?, ?)
            ''', (user_id, name, phone, datetime.now().isoformat()))
            conn.commit()
            
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            user = cursor.fetchone()
        
        conn.close()
        return user
    
    def update_user_balance(self, user_id, amount):
        """Atualiza o saldo do usuário"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users SET balance = balance + ? WHERE user_id = ?
        ''', (amount, user_id))
        
        conn.commit()
        conn.close()
    
    def create_pix_transaction(self, user_id, amount):
        """Cria uma transação PIX"""
        transaction_id = str(uuid.uuid4())[:8]
        expiry_date = datetime.now() + timedelta(minutes=30)
        
        # Gerar chave PIX fictícia (em produção, usar API real)
        pix_key = f"00020101021226830014BR.GOV.BCB.PIX2561qrcodespix.sejaefi.com.br/v2/{transaction_id}5204000053039865802BR5905EFISA6008SAOPAULO62070503***6304E477"
        
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO pix_transactions 
            (transaction_id, user_id, amount, qr_code, pix_key, expiry_date, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (transaction_id, user_id, amount, pix_key, pix_key, expiry_date.isoformat(), datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        return transaction_id, pix_key, expiry_date
    
    def get_products(self):
        """Obtém todos os produtos ativos"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM products WHERE active = 1')
        products = cursor.fetchall()
        
        conn.close()
        return products
    
    def get_product(self, product_id):
        """Obtém um produto específico"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM products WHERE product_id = ?', (product_id,))
        product = cursor.fetchone()
        
        conn.close()
        return product
    
    def purchase_product(self, user_id, product_id):
        """Processa a compra de um produto"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Verificar saldo e produto
        cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
        user_balance = cursor.fetchone()[0]
        
        cursor.execute('SELECT * FROM products WHERE product_id = ?', (product_id,))
        product = cursor.fetchone()
        
        if not product or product[5] <= 0:  # stock
            conn.close()
            return False, "Produto indisponível"
        
        if user_balance < product[2]:  # price
            conn.close()
            return False, "Saldo insuficiente"
        
        # Processar compra
        purchase_id = str(uuid.uuid4())[:8]
        
        cursor.execute('''
            INSERT INTO purchases (purchase_id, user_id, product_id, amount, purchase_date, product_data)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (purchase_id, user_id, product_id, product[2], datetime.now().isoformat(), json.dumps({
            "name": product[1],
            "email": f"user_{user_id}@exemplo.com",
            "password": f"pass_{purchase_id}",
            "instructions": f"Baixe o app na Play Store/App Store e use:\nEmail: user_{user_id}@exemplo.com\nSenha: pass_{purchase_id}"
        })))
        
        # Atualizar saldo e estoque
        cursor.execute('UPDATE users SET balance = balance - ? WHERE user_id = ?', (product[2], user_id))
        cursor.execute('UPDATE products SET stock = stock - 1 WHERE product_id = ?', (product_id,))
        
        conn.commit()
        conn.close()
        
        return True, purchase_id
    
    def get_user_purchases(self, user_id):
        """Obtém histórico de compras do usuário"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT p.purchase_id, pr.name, p.amount, p.purchase_date, p.product_data
            FROM purchases p
            JOIN products pr ON p.product_id = pr.product_id
            WHERE p.user_id = ?
            ORDER BY p.purchase_date DESC
        ''', (user_id,))
        
        purchases = cursor.fetchall()
        conn.close()
        return purchases
    
    def convert_bonus_to_balance(self, user_id, amount):
        """Converte bônus em saldo"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('SELECT bonus FROM users WHERE user_id = ?', (user_id,))
        bonus = cursor.fetchone()[0]
        
        if bonus >= amount:
            cursor.execute('''
                UPDATE users 
                SET bonus = bonus - ?, balance = balance + ?
                WHERE user_id = ?
            ''', (amount, amount, user_id))
            conn.commit()
            conn.close()
            return True
        
        conn.close()
        return False
    
    def check_flood_control(self, user_id):
        """Verifica controle de flood"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        now = datetime.now()
        
        cursor.execute('SELECT * FROM flood_control WHERE user_id = ?', (user_id,))
        flood_data = cursor.fetchone()
        
        if not flood_data:
            cursor.execute('''
                INSERT INTO flood_control (user_id, last_message_time, flood_count)
                VALUES (?, ?, 1)
            ''', (user_id, now.isoformat()))
            conn.commit()
            conn.close()
            return True, 0
        
        last_time = datetime.fromisoformat(flood_data[1])
        blocked_until = datetime.fromisoformat(flood_data[3]) if flood_data[3] else None
        
        if blocked_until and now < blocked_until:
            remaining = int((blocked_until - now).total_seconds())
            conn.close()
            return False, remaining
        
        # Reset flood count se passou mais de 10 segundos
        if (now - last_time).total_seconds() > 10:
            cursor.execute('''
                UPDATE flood_control 
                SET flood_count = 1, last_message_time = ?, blocked_until = NULL
                WHERE user_id = ?
            ''', (now.isoformat(), user_id))
        else:
            new_count = flood_data[2] + 1
            if new_count > 3:  # Limite de 3 mensagens
                block_until = now + timedelta(seconds=6 * new_count)
                cursor.execute('''
                    UPDATE flood_control 
                    SET flood_count = ?, last_message_time = ?, blocked_until = ?
                    WHERE user_id = ?
                ''', (new_count, now.isoformat(), block_until.isoformat(), user_id))
                conn.commit()
                conn.close()
                return False, 6 * new_count
            else:
                cursor.execute('''
                    UPDATE flood_control 
                    SET flood_count = ?, last_message_time = ?
                    WHERE user_id = ?
                ''', (new_count, now.isoformat(), user_id))
        
        conn.commit()
        conn.close()
        return True, 0