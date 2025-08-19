import Database from 'better-sqlite3';

const db = new Database('/workspace/data.sqlite');

db.pragma('journal_mode = WAL');

db.exec(`
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  wa_id TEXT UNIQUE NOT NULL,
  name TEXT DEFAULT '',
  phone TEXT DEFAULT '',
  telegram_id TEXT DEFAULT '',
  balance_cents INTEGER DEFAULT 0,
  bonus_cents INTEGER DEFAULT 0,
  role TEXT DEFAULT 'cliente',
  referrer TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS products (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  code TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  description TEXT NOT NULL,
  price_cents INTEGER NOT NULL,
  stock INTEGER DEFAULT 0,
  warranty_days INTEGER DEFAULT 30
);

CREATE TABLE IF NOT EXISTS orders (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  order_id TEXT UNIQUE NOT NULL,
  wa_id TEXT NOT NULL,
  product_code TEXT,
  amount_cents INTEGER NOT NULL,
  status TEXT NOT NULL,
  created_at INTEGER NOT NULL,
  expires_at INTEGER NOT NULL,
  paid_at INTEGER
);

CREATE TABLE IF NOT EXISTS order_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  order_id TEXT NOT NULL,
  content TEXT NOT NULL
);
`);

export function upsertUser({ waId, name, phone }) {
  const stmt = db.prepare(`INSERT INTO users (wa_id, name, phone)
    VALUES (@waId, @name, @phone)
    ON CONFLICT(wa_id) DO UPDATE SET name=excluded.name, phone=excluded.phone`);
  stmt.run({ waId, name: name || '', phone: phone || '' });
}

export function getUser(waId) {
  return db.prepare('SELECT * FROM users WHERE wa_id = ?').get(waId);
}

export function ensureUser(waId) {
  let user = getUser(waId);
  if (!user) {
    db.prepare('INSERT INTO users (wa_id) VALUES (?)').run(waId);
    user = getUser(waId);
  }
  return user;
}

export function addBalance(waId, cents) {
  db.prepare('UPDATE users SET balance_cents = balance_cents + ? WHERE wa_id = ?').run(cents, waId);
}

export function deductBalance(waId, cents) {
  db.prepare('UPDATE users SET balance_cents = balance_cents - ? WHERE wa_id = ?').run(cents, waId);
}

export function addBonus(waId, cents) {
  db.prepare('UPDATE users SET bonus_cents = bonus_cents + ? WHERE wa_id = ?').run(cents, waId);
}

export function deductBonus(waId, cents) {
  db.prepare('UPDATE users SET bonus_cents = bonus_cents - ? WHERE wa_id = ?').run(cents, waId);
}

export function listProducts() {
  return db.prepare('SELECT * FROM products ORDER BY id ASC').all();
}

export function getProductByCode(code) {
  return db.prepare('SELECT * FROM products WHERE code = ?').get(code);
}

export function seedProductsIfEmpty() {
  const count = db.prepare('SELECT COUNT(*) as c FROM products').get().c;
  if (count === 0) {
    const insert = db.prepare('INSERT INTO products (code, name, description, price_cents, stock, warranty_days) VALUES (?, ?, ?, ?, ?, ?)');
    insert.run('PROD1', 'Produto 1', 'Descrição do Produto 1', 990, 100, 30);
    insert.run('PROD2', 'Produto 2', 'Descrição do Produto 2', 1990, 50, 30);
    insert.run('PROD3', 'Produto 3', 'Descrição do Produto 3', 2990, 20, 30);
    insert.run('PROD4', 'Produto 4', 'Descrição do Produto 4', 4990, 10, 30);
  }
}

export function createOrder({ orderId, waId, productCode, amountCents, expiresAt }) {
  db.prepare(`INSERT INTO orders (order_id, wa_id, product_code, amount_cents, status, created_at, expires_at)
    VALUES (?, ?, ?, ?, 'pending', ?, ?)`)
    .run(orderId, waId, productCode || null, amountCents, Date.now(), expiresAt);
}

export function markOrderPaid(orderId) {
  db.prepare(`UPDATE orders SET status='paid', paid_at=? WHERE order_id=?`).run(Date.now(), orderId);
}

export function expireOrder(orderId) {
  db.prepare(`UPDATE orders SET status='expired' WHERE order_id=? AND status='pending'`).run(orderId);
}

export function getOrder(orderId) {
  return db.prepare('SELECT * FROM orders WHERE order_id = ?').get(orderId);
}

export function listUserOrders(waId) {
  return db.prepare('SELECT * FROM orders WHERE wa_id = ? ORDER BY id DESC').all(waId);
}

export function addOrderItem(orderId, content) {
  db.prepare('INSERT INTO order_items (order_id, content) VALUES (?, ?)').run(orderId, content);
}

export function listOrderItems(orderId) {
  return db.prepare('SELECT content FROM order_items WHERE order_id = ?').all(orderId).map(r => r.content);
}

export default db;

