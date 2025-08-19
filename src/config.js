import dotenv from 'dotenv';

dotenv.config();

export const config = {
	port: parseInt(process.env.PORT || '3000', 10),
	botName: process.env.BOT_NAME || 'JOÃOZINHO STORE BOT',
	supportName: process.env.SUPPORT_NAME || 'JOÃO',
	supportNumber: process.env.SUPPORT_NUMBER || '5544998312326',
	baseUrl: process.env.BASE_URL || '',
	pix: {
		provider: (process.env.EFI_CLIENT_ID && process.env.EFI_CLIENT_SECRET) ? 'efi' : 'mock',
		efi: {
			clientId: process.env.EFI_CLIENT_ID || '',
			clientSecret: process.env.EFI_CLIENT_SECRET || '',
			certPath: process.env.EFI_CERT_PATH || '',
			pixKey: process.env.EFI_PIX_KEY || '',
			webhookSecret: process.env.EFI_WEBHOOK_SECRET || ''
		}
	},
	rateLimitSeconds: 6,
	bonusConversionTimeoutSec: 80
};

import dotenv from 'dotenv';

dotenv.config();

export const config = {
	port: parseInt(process.env.PORT || '3000', 10),
	botName: process.env.BOT_NAME || 'JOÃOZINHO STORE BOT',
	supportName: process.env.SUPPORT_NAME || 'JOÃO',
	supportNumber: process.env.SUPPORT_NUMBER || '5544998312326',
	baseUrl: process.env.BASE_URL || '',
	pix: {
		provider: (process.env.EFI_CLIENT_ID && process.env.EFI_CLIENT_SECRET) ? 'efi' : 'mock',
		efi: {
			clientId: process.env.EFI_CLIENT_ID || '',
			clientSecret: process.env.EFI_CLIENT_SECRET || '',
			certPath: process.env.EFI_CERT_PATH || '',
			pixKey: process.env.EFI_PIX_KEY || '',
			webhookSecret: process.env.EFI_WEBHOOK_SECRET || ''
		}
	},
	rateLimitSeconds: 6,
	bonusConversionTimeoutSec: 80
};

