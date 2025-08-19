// Simple in-memory state for anti-flood and pending actions
import { config } from './config.js';

const lastRequestAtByUser = new Map();
const pendingContexts = new Map();

export function canProceed(waId) {
	const now = Date.now();
	const last = lastRequestAtByUser.get(waId) || 0;
	if (now - last < config.rateLimitSeconds * 1000) {
		return false;
	}
	lastRequestAtByUser.set(waId, now);
	return true;
}

export function setPending(waId, ctx) {
	pendingContexts.set(waId, { ...ctx, createdAt: Date.now() });
}

export function getPending(waId) {
	return pendingContexts.get(waId);
}

export function clearPending(waId) {
	pendingContexts.delete(waId);
}

