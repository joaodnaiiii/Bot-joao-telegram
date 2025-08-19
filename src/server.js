import express from 'express';
import { config } from './config.js';

export function createServer({ onPixPaid, onPixExpired }) {
	const app = express();
	app.use(express.json({ limit: '1mb' }));

	// Mock PIX webhook endpoints
	app.post('/webhooks/pix/paid', (req, res) => {
		const { orderId } = req.body || {};
		if (!orderId) return res.status(400).json({ error: 'orderId required' });
		onPixPaid?.(orderId);
		res.json({ ok: true });
	});

	app.post('/webhooks/pix/expired', (req, res) => {
		const { orderId } = req.body || {};
		if (!orderId) return res.status(400).json({ error: 'orderId required' });
		onPixExpired?.(orderId);
		res.json({ ok: true });
	});

	const server = app.listen(config.port, () => {
		console.log(`HTTP server listening on :${config.port}`);
	});

	return { app, server };
}

