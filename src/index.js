import makeWASocket, { useMultiFileAuthState, delay, DisconnectReason, fetchLatestBaileysVersion, makeCacheableSignalKeyStore } from 'baileys';
import { config } from './config.js';
import db, { ensureUser, seedProductsIfEmpty, listProducts, getProductByCode, addBalance, createOrder, markOrderPaid, expireOrder, getOrder, addOrderItem, listUserOrders } from './db.js';
import { MockPixProvider } from './pix/mockProvider.js';
import { mainMenu, addBalanceMenu, generatingPix, pixChargeMessage, pixExpiredMessage, premiumHeader, insufficientBalance, productDetail, myAccount, bonusPrompt, confirmConversion, supportMessage, floodWarning } from './menu.js';
import { canProceed, setPending, getPending, clearPending } from './state.js';
import { randomBytes } from 'crypto';
import { createServer } from './server.js';

const pix = new MockPixProvider();

function parseCommand(text) {
	return (text || '').trim();
}

function productButtons(products) {
	return products.map(p => ({ buttonId: `BUY:${p.code}`, buttonText: { displayText: p.name }, type: 1 }));
}

function menuButtons() {
	return [
		{ buttonId: 'MENU_ADD_SALDO', buttonText: { displayText: '💸 Adicionar Saldo' }, type: 1 },
		{ buttonId: 'MENU_PREMIUM', buttonText: { displayText: '🛍️ Assinaturas Premium' }, type: 1 },
		{ buttonId: 'MENU_ASSOCIADO', buttonText: { displayText: '💼 Area do Associado' }, type: 1 },
		{ buttonId: 'MENU_SUPORTE', buttonText: { displayText: '🆘 Contato do Suporte' }, type: 1 }
	];
}

function addSaldoButtons() {
	return [
		{ buttonId: 'PIX_500', buttonText: { displayText: '💠 PIX R$ 5,00' }, type: 1 },
		{ buttonId: 'PIX_1000', buttonText: { displayText: '💠 PIX R$ 10,00' }, type: 1 },
		{ buttonId: 'PIX_2000', buttonText: { displayText: '💠 PIX R$ 20,00' }, type: 1 },
		{ buttonId: 'PIX_OTHER', buttonText: { displayText: '💠 DIGITE OUTRO VALOR' }, type: 1 }
	];
}

async function sendButtons(sock, jid, text, buttons) {
	await sock.sendMessage(jid, { text, buttons, footer: config.botName });
}

async function startBot() {
	const { state, saveCreds } = await useMultiFileAuthState('/workspace/baileys_auth');
	const { version, isLatest } = await fetchLatestBaileysVersion();
	console.log(`using WA v${version.join('.')}, isLatest: ${isLatest}`);

	const sock = makeWASocket({
		version,
		auth: {
			signalKeyStore: makeCacheableSignalKeyStore(state.keys, console),
			...state
		},
		printQRInTerminal: true
	});

	sock.ev.on('creds.update', saveCreds);

	seedProductsIfEmpty();

	createServer({
		onPixPaid: async (orderId) => {
			const order = getOrder(orderId);
			if (!order || order.status !== 'pending') return;
			markOrderPaid(orderId);
			addBalance(order.wa_id, order.amount_cents);
			await sock.sendMessage(order.wa_id, { text: '✅ Pagamento confirmado! Seu saldo foi creditado em até 1 minuto. Obrigado!' });
		},
		onPixExpired: async (orderId) => {
			const order = getOrder(orderId);
			if (!order || order.status !== 'pending') return;
			expireOrder(orderId);
			await sock.sendMessage(order.wa_id, { text: pixExpiredMessage() });
		}
	});

	sock.ev.on('connection.update', async (update) => {
		const { connection, lastDisconnect } = update;
		if (connection === 'close') {
			const shouldReconnect = (lastDisconnect?.error)?.output?.statusCode !== DisconnectReason.loggedOut;
			console.log('connection closed due to ', lastDisconnect?.error, ', reconnecting ', shouldReconnect);
			if (shouldReconnect) startBot();
		}
		else if (connection === 'open') {
			console.log('Connected to WhatsApp');
		}
	});

	sock.ev.on('messages.upsert', async ({ messages }) => {
		const msg = messages?.[0];
		if (!msg?.key?.remoteJid || msg.key.fromMe) return;
		const jid = msg.key.remoteJid;
		const waId = jid;

		if (!canProceed(waId)) {
			await sock.sendMessage(jid, { text: floodWarning(6) });
			return;
		}

		ensureUser(waId);

		const text = parseCommand(
			msg.message?.conversation ||
			msg.message?.extendedTextMessage?.text ||
			msg.message?.buttonsResponseMessage?.selectedDisplayText ||
			msg.message?.templateButtonReplyMessage?.selectedDisplayText ||
			msg.message?.interactiveResponseMessage?.body?.text || ''
		);
		const selectedId = msg.message?.buttonsResponseMessage?.selectedButtonId || msg.message?.interactiveResponseMessage?.nativeFlowResponseMessage?.paramsJson || '';

		if (/^oi$|^menu$|^start$/i.test(text) || text === '') {
			const user = ensureUser(waId);
			await sendButtons(sock, jid, mainMenu({ number: jid, balanceCents: user.balance_cents }), menuButtons());
			return;
		}

		// Handle menu buttons
		if (text.startsWith('💸 Adicionar Saldo') || selectedId === 'MENU_ADD_SALDO') {
			await sendButtons(sock, jid, addBalanceMenu(), addSaldoButtons());
			return;
		}
		if (text.startsWith('🛍️ Assinaturas Premium') || selectedId === 'MENU_PREMIUM') {
			const user = ensureUser(waId);
			const products = listProducts().slice(0, 4);
			await sendButtons(sock, jid, premiumHeader({ number: jid, balanceCents: user.balance_cents }), productButtons(products));
			return;
		}
		if (text.startsWith('💼 Area do Associado') || selectedId === 'MENU_ASSOCIADO') {
			const user = ensureUser(waId);
			await sock.sendMessage(jid, { text: myAccount({
				name: user.name,
				waId: user.wa_id,
				phone: user.phone,
				referrer: user.referrer,
				role: user.role,
				balanceCents: user.balance_cents,
				bonusCents: user.bonus_cents
			}) });
			await sendButtons(sock, jid, 'Escolha uma opção da sua conta:', [
				{ buttonId: 'ACC_COMPRAS', buttonText: { displayText: '🛍️ Minhas Compras' }, type: 1 },
				{ buttonId: 'ACC_RESgATAR', buttonText: { displayText: '💰 Resgatar Saldo' }, type: 1 }
			]);
			return;
		}
		if (text.startsWith('🆘 Contato do Suporte') || selectedId === 'MENU_SUPORTE') {
			await sock.sendMessage(jid, { text: supportMessage({ name: config.supportName, number: config.supportNumber }) });
			return;
		}

		// Add balance options
		if (text.includes('PIX R$ 5,00') || selectedId === 'PIX_500') {
			await handleCreatePixCharge(sock, jid, waId, 500);
			return;
		}
		if (text.includes('PIX R$ 10,00') || selectedId === 'PIX_1000') {
			await handleCreatePixCharge(sock, jid, waId, 1000);
			return;
		}
		if (text.includes('PIX R$ 20,00') || selectedId === 'PIX_2000') {
			await handleCreatePixCharge(sock, jid, waId, 2000);
			return;
		}
		if (text.includes('DIGITE OUTRO VALOR') || selectedId === 'PIX_OTHER') {
			setPending(waId, { type: 'ENTER_PIX_AMOUNT', expiresAt: Date.now() + 120000 });
			await sock.sendMessage(jid, { text: 'Digite o valor em reais (ex: 7.50):' });
			return;
		}

		const pending = getPending(waId);
		if (pending?.type === 'ENTER_PIX_AMOUNT') {
			const amount = parseFloat(text.replace(',', '.'));
			if (isNaN(amount) || amount <= 0) {
				await sock.sendMessage(jid, { text: 'Valor inválido. Tente novamente.' });
				return;
			}
			clearPending(waId);
			await handleCreatePixCharge(sock, jid, waId, Math.round(amount * 100));
			return;
		}

		// Product button buy
		if (text.startsWith('BUY:') || msg.message?.buttonsResponseMessage?.selectedButtonId?.startsWith('BUY:')) {
			const code = (text.startsWith('BUY:') ? text.split(':')[1] : msg.message.buttonsResponseMessage.selectedButtonId.split(':')[1]);
			await showProductDetail(sock, jid, waId, code);
			return;
		}

		if (/^🛒 Comprar$/.test(text)) {
			const last = getPending(waId);
			if (!last || last.type !== 'VIEW_PRODUCT') return;
			await startProductPurchase(sock, jid, waId, last.productCode);
			return;
		}

		if (selectedId === 'ACC_COMPRAS' || text.includes('Minhas Compras')) {
			await sendPurchaseHistory(sock, jid, waId);
			return;
		}
		if (selectedId === 'ACC_RESgATAR' || text.includes('Resgatar Saldo')) {
			const user = ensureUser(waId);
			await sock.sendMessage(jid, { text: bonusPrompt(user.bonus_cents) });
			setPending(waId, { type: 'BONUS_ENTER', expiresAt: Date.now() + 80000 });
			return;
		}
		if (pending?.type === 'BONUS_ENTER') {
			const amount = Math.round(parseFloat(text.replace(',', '.')) * 100);
			if (isNaN(amount) || amount <= 0) {
				await sock.sendMessage(jid, { text: 'Valor inválido.' });
				return;
			}
			setPending(waId, { type: 'BONUS_CONFIRM', amountCents: amount, expiresAt: Date.now() + 60000 });
			await sendButtons(sock, jid, confirmConversion(amount), [
				{ buttonId: 'CONFIRM_BONUS', buttonText: { displayText: 'Confirmar ✅' }, type: 1 },
				{ buttonId: 'CANCEL_BONUS', buttonText: { displayText: 'Cancelar ❌' }, type: 1 }
			]);
			return;
		}
		if (selectedId === 'CONFIRM_BONUS') {
			const ctx = getPending(waId);
			if (!ctx || ctx.type !== 'BONUS_CONFIRM') return;
			const user = ensureUser(waId);
			const amount = Math.min(ctx.amountCents, user.bonus_cents);
			if (amount <= 0) {
				await sock.sendMessage(jid, { text: 'Sem bônus disponível.' });
				clearPending(waId);
				return;
			}
			// move bonus to balance
			db.prepare('UPDATE users SET bonus_cents = bonus_cents - ?, balance_cents = balance_cents + ? WHERE wa_id = ?').run(amount, amount, waId);
			await sock.sendMessage(jid, { text: '✅ Bônus convertido em saldo com sucesso!' });
			clearPending(waId);
			return;
		}
		if (selectedId === 'CANCEL_BONUS') {
			clearPending(waId);
			await sock.sendMessage(jid, { text: 'Operação cancelada.' });
			return;
		}
	});

	async function showProductDetail(sock, jid, waId, code) {
		const product = getProductByCode(code);
		if (!product) return sock.sendMessage(jid, { text: 'Produto não encontrado.' });
		await sock.sendMessage(jid, { text: productDetail({ name: product.name, priceCents: product.price_cents, stock: product.stock, warrantyDays: product.warranty_days }) });
		setPending(waId, { type: 'VIEW_PRODUCT', productCode: code });
		await sendButtons(sock, jid, 'Opções:', [{ buttonId: 'BUY_NOW', buttonText: { displayText: '🛒 Comprar' }, type: 1 }]);
	}

	async function startProductPurchase(sock, jid, waId, code) {
		const user = ensureUser(waId);
		const product = getProductByCode(code);
		if (!product) return sock.sendMessage(jid, { text: 'Produto não encontrado.' });
		if ((user.balance_cents || 0) < product.price_cents) {
			await sock.sendMessage(jid, { text: insufficientBalance() });
			return;
		}
		// deduct and deliver
		db.prepare('UPDATE users SET balance_cents = balance_cents - ? WHERE wa_id = ?').run(product.price_cents, waId);
		const orderId = randomBytes(8).toString('hex');
		createOrder({ orderId, waId, productCode: code, amountCents: product.price_cents, expiresAt: Date.now() + 1 });
		addOrderItem(orderId, `Email: cliente@example.com`);
		addOrderItem(orderId, `Senha: senha123`);
		await sock.sendMessage(jid, { text: `✅ Compra confirmada!\n\nProduto: ${product.name}\nPreço: R$ ${(product.price_cents/100).toFixed(2).replace('.', ',')}` });
		await sock.sendMessage(jid, { text: 'Siga as instruções para baixar o app na App Store/Play Store e aplicar as credenciais enviadas.' });
	}

	async function handleCreatePixCharge(sock, jid, waId, amountCents) {
		await sock.sendMessage(jid, { text: generatingPix() });
		const charge = await pix.createCharge({ amountCents, expiresMinutes: 30 });
		const orderId = charge.id;
		createOrder({ orderId, waId, productCode: null, amountCents, expiresAt: charge.expiresAt });
		const b64 = (charge.qrPng || '').split(',')[1];
		const buf = b64 ? Buffer.from(b64, 'base64') : undefined;
		if (buf) {
			await sock.sendMessage(jid, { image: buf, caption: pixChargeMessage({ id: orderId, amountCents, displayDue: charge.displayDue }) });
		}
		await sock.sendMessage(jid, { text: charge.code });
		// schedule expiration
		setTimeout(async () => {
			const order = getOrder(orderId);
			if (order && order.status === 'pending' && Date.now() >= order.expires_at) {
				expireOrder(orderId);
				await sock.sendMessage(jid, { text: pixExpiredMessage() });
			}
		}, Math.max(1000, charge.expiresAt - Date.now() + 1000));
	}
}

async function sendPurchaseHistory(sock, jid, waId) {
	const orders = listUserOrders(waId);
	const lines = [];
	lines.push('Minhas Compras');
	lines.push('');
	for (const o of orders) {
		const items = listOrderItems(o.order_id);
		const dt = new Date(o.created_at);
		lines.push(`- ID: ${o.order_id}`);
		lines.push(`  Data: ${dt.toLocaleString('pt-BR')}`);
		lines.push(`  Valor: R$ ${(o.amount_cents/100).toFixed(2).replace('.', ',')}`);
		lines.push(`  Status: ${o.status}`);
		if (o.product_code) lines.push(`  Produto: ${o.product_code}`);
		if (items.length) {
			lines.push('  Itens:');
			for (const it of items) lines.push(`    - ${it}`);
		}
		lines.push('');
	}
	const buf = Buffer.from(lines.join('\n'), 'utf8');
	await sock.sendMessage(jid, { document: buf, mimetype: 'text/plain', fileName: 'minhas-compras.txt', caption: 'Seu histórico de compras' });
}

startBot().catch((e) => console.error('Fatal:', e));