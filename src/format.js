export function centsToBRL(cents) {
	const brl = (cents / 100).toFixed(2);
	return `R$ ${brl.replace('.', ',')}`;
}

export function maskPhone(waIdOrPhone) {
	const digits = waIdOrPhone.replace(/[^0-9]/g, '');
	return `+${digits}`;
}

