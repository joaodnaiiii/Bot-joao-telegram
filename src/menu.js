import { centsToBRL } from './format.js';
import { config } from './config.js';

export function mainMenu({ number, balanceCents }) {
	return [
		`🤖 ${config.botName}`,
		'',
		'🥇Nosso bot permite que você encontre diversos produtos e serviços, oferecendo um ótimo custo-beneficio na hora de comprar, assim você encontrará o item desejado pelo menor preço.',
		'',
		'ℹ️ Seus Dados:',
		`💠 Número: ${number || ''}`,
		`💸 Saldo Atual: ${centsToBRL(balanceCents || 0)}`,
		'',
		'Escolha uma opção:',
		'',
		'💸 Adicionar Saldo',
		'🛍️ Assinaturas Premium',
		'💼 Area do Associado',
		'🆘 Contato do Suporte'
	].join('\n');
}

export function addBalanceMenu() {
	return [
		'💸 MENU DE OPÇÃO DE PIX 💸',
		'',
		'Escolha um dos valores disponíveis para recarregar sua conta ou selecione "Digite outro valor" para inserir um valor personalizado.',
		'',
		'💠 PIX R$ 5,00',
		'💠 PIX R$ 10,00',
		'💠 PIX R$ 20,00',
		'💠 DIGITE OUTRO VALOR'
	].join('\n');
}

export function generatingPix() {
	return '*⏳ Gerando PIX...*\n\nAguarde um momento! 💰';
}

export function pixChargeMessage({ id, amountCents, displayDue }) {
	return [
		'*💰 ADICIONAR SALDO COM PIX AUTOMÁTICO 💠*',
		'',
		'⚠️ Você está prestes a adicionar saldo ao bot!',
		'',
		'Escaneie o *QR Code* acima ou utilize o *código PIX* enviado abaixo.',
		'',
		'O PIX expira em *30 minutos*, pague dentro do prazo.',
		'',
		'O saldo será creditado em até *1 \nminuto* após o pagamento.',
		'',
		'*⚠️ ADICIONE APENAS O QUE FOR USAR!*',
		'_Não realizamos reembolsos._',
		'',
		'━━━━━━━━❪❃❫━━━━━━━━',
		'',
		'*🆔 ID da Compra:* ' + id,
		`*💰 Valor:* ${centsToBRL(amountCents)}`,
		`*📅 Vencimento:* ${displayDue}`,
		'',
		'━━━━━━━━❪❃❫━━━━━━━━',
		'',
		'*🔑 O código PIX foi enviado abaixo para facilitar o pagamento!*'
	].join('\n');
}

export function pixExpiredMessage() {
	return '*⚠️ Solicitação Negada!*\n\nDesculpe, sua recarga falhou porque o *PIX não foi pago dentro do prazo*. ⏳❌';
}

export function premiumHeader({ wallet, number, balanceCents }) {
	return [
		'🥇 Somos a solução para o mercado digital, disponibilizando um bot moderno que permite que o cliente receba pelo produto / serviço desejado. Tudo isso com praticidade e segurança.',
		'',
		'🏦 Carteira:',
		`💠 Número: ${number || ''}`,
		`💰 Saldo Atual: ${centsToBRL(balanceCents || 0)}`
	].join('\n');
}

export function insufficientBalance() {
	return '*❌ Saldo Insuficiente!*\n\nSeu saldo atual não é suficiente para concluir esta compra. Faça uma *recarga* e tente novamente! 💰';
}

export function productDetail({ name, priceCents, stock, warrantyDays }) {
	return [
		'◎ ══════ ❈ ══════ ◎',
		`⚜️ACESSO: ${name} ⚜️`,
		'',
		`💵| Preço: ${centsToBRL(priceCents)}`,
		'💼| Saldo Atual: 0,00',
		`📥| Estoque Disponível: ${stock}`,
		'',
		'🗒 Descrição: Aviso Importante:',
		'Informamos que não realizamos reembolsos via Pix, apenas em créditos no bot, correspondendo aos dias restantes até o vencimento.',
		'Agradecemos pela compreensão e desejamos boas compras!',
		'',
		'Obs: O prazo de entrega é até 24 horas.',
		'Obs: ERRO DE 12 MESES OU ERRO DE CONVITE QUE NAO CHEGOU, AVISAR EM ATÉ 2 DIAS NO MÁXIMO, APÓS ISSO PERDE SUPORTE E QUALQUER TIPO DE AJUDA.',
		'Obs: Olhe atentamente a o texto da compra.',
		'',
		`♻️ Garantia: ${warrantyDays}`,
		'◎ ══════ ❈ ══════ ◎'
	].join('\n');
}

export function myAccount({ name, waId, phone, referrer, role, balanceCents, bonusCents }) {
	return [
		'🗒️ SUA CONTA',
		`👤 Nome: ${name || ''}`,
		`🆔 Telegram ID: ${waId || ''}`,
		`📞 Número: ${phone || ''}`,
		'',
		`📢 Indicador: ${referrer || ''}`,
		`Cargo: ${role || ''}`,
		`Saldo: ${centsToBRL(balanceCents || 0)}`,
		`Bônus: ${centsToBRL(bonusCents || 0)}`
	].join('\n');
}

export function bonusPrompt(amountCents) {
	return `*⏳ Você possui ${centsToBRL(amountCents)} em bônus.*\nInforme a quantidade que deseja converter em saldo.\nVocê tem *80 segundos* para responder.`;
}

export function confirmConversion(amountCents) {
	return ['❓ Confirmar Conversão ', '*_____________________________*', '', `Deseja converter R$: ${isNaN(amountCents) ? 'NaN' : (amountCents/100).toFixed(2).replace('.', ',')} em saldo?`].join('\n');
}

export function supportMessage({ name, number }) {
	return [
		'*👤 CONTATO DO SUPORTE 👤*',
		'',
		'*⚠️ Este é o número do responsável ou suporte deste bot.*',
		'',
		'*⚠️ Dúvidas sobre o material vendido?* Entre em contato apenas com este número!',
		'',
		`*${name}* - meu número ${number}`
	].join('\n');
}

export function floodWarning(seconds) {
	return `*⚠️ Atenção!*\n\nPare de floodar! Suas solicitações serão ignoradas pelos próximos *${seconds} segundos* (acumulativo). ⏳`;
}

