import { format } from 'date-fns';
import { randomBytes } from 'crypto';
import QRCode from 'qrcode';

function centsToBRL(cents) {
	return (cents / 100).toFixed(2).replace('.', ',');
}

export class MockPixProvider {
	constructor() {}

	async createCharge({ amountCents, expiresMinutes }) {
		const id = randomBytes(8).toString('hex');
		const expiresAt = Date.now() + expiresMinutes * 60 * 1000;
		const brl = centsToBRL(amountCents);
		const code = `00020101021226830014BR.GOV.BCB.PIX2561qrcodespix.sejaefi.com.br/v2/${id}5204000053039865802BR5905EFISA6008SAOPAULO62070503***6304E477`;
		const qrPng = await QRCode.toDataURL(code);
		return {
			id,
			expiresAt,
			code,
			qrPng,
			displayAmount: `R$ ${brl}`,
			displayDue: format(expiresAt, "dd/MM/yyyy 'às' HH:mm:ss")
		};
	}

	// No-op in mock. Real provider would verify signatures.
	verifyWebhookSignature() {
		return true;
	}
}

