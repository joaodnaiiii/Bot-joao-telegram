import mercadopago
import qrcode
import io
import base64
import uuid
import requests
from datetime import datetime, timedelta
from config import MERCADO_PAGO_ACCESS_TOKEN, MERCADO_PAGO_PUBLIC_KEY
from database import db
import logging

logger = logging.getLogger(__name__)

class PaymentSystem:
    def __init__(self):
        self.mp = mercadopago.SDK(MERCADO_PAGO_ACCESS_TOKEN)
        
    def create_pix_payment(self, user_id, amount, description="Recarga de saldo"):
        """Cria um pagamento PIX e retorna QR Code"""
        try:
            # Gerar ID único para o pagamento
            payment_id = str(uuid.uuid4())
            
            # Dados do pagamento
            payment_data = {
                "transaction_amount": float(amount),
                "description": description,
                "payment_method_id": "pix",
                "payer": {
                    "email": f"user{user_id}@bot.com",
                    "identification": {
                        "type": "CPF",
                        "number": "00000000000"
                    }
                },
                "external_reference": payment_id,
                "date_of_expiration": (datetime.now() + timedelta(minutes=30)).isoformat(),
                "notification_url": "https://your-webhook-url.com/webhook"
            }
            
            # Criar pagamento no Mercado Pago
            payment_response = self.mp.payment().create(payment_data)
            
            if payment_response["status"] == 201:
                payment_info = payment_response["response"]
                
                # Obter dados do PIX
                pix_data = payment_info.get("point_of_interaction", {}).get("transaction_data", {})
                qr_code_base64 = pix_data.get("qr_code_base64", "")
                qr_code = pix_data.get("qr_code", "")
                
                if not qr_code_base64 and qr_code:
                    # Gerar QR Code se não fornecido
                    qr_code_base64 = self.generate_qr_code(qr_code)
                
                # Salvar transação no banco
                transaction_id = db.create_transaction(
                    user_id=user_id,
                    transaction_type='recharge',
                    amount=amount,
                    description=description,
                    payment_id=payment_info["id"]
                )
                
                return {
                    "success": True,
                    "payment_id": payment_info["id"],
                    "transaction_id": transaction_id,
                    "qr_code_base64": qr_code_base64,
                    "qr_code": qr_code,
                    "amount": amount,
                    "expires_at": payment_info.get("date_of_expiration"),
                    "status": payment_info.get("status")
                }
            else:
                logger.error(f"Erro ao criar pagamento: {payment_response}")
                return {"success": False, "error": "Erro ao processar pagamento"}
                
        except Exception as e:
            logger.error(f"Erro no sistema de pagamento: {e}")
            return {"success": False, "error": str(e)}
    
    def generate_qr_code(self, data):
        """Gera QR Code em base64"""
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(data)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Converter para base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            return img_base64
            
        except Exception as e:
            logger.error(f"Erro ao gerar QR Code: {e}")
            return None
    
    def check_payment_status(self, payment_id):
        """Verifica status do pagamento"""
        try:
            payment_response = self.mp.payment().get(payment_id)
            
            if payment_response["status"] == 200:
                payment_info = payment_response["response"]
                return {
                    "success": True,
                    "status": payment_info.get("status"),
                    "status_detail": payment_info.get("status_detail"),
                    "amount": payment_info.get("transaction_amount"),
                    "external_reference": payment_info.get("external_reference")
                }
            else:
                return {"success": False, "error": "Pagamento não encontrado"}
                
        except Exception as e:
            logger.error(f"Erro ao verificar status: {e}")
            return {"success": False, "error": str(e)}
    
    def process_webhook(self, webhook_data):
        """Processa webhook do Mercado Pago"""
        try:
            if webhook_data.get("type") == "payment":
                payment_id = webhook_data.get("data", {}).get("id")
                
                if payment_id:
                    payment_status = self.check_payment_status(payment_id)
                    
                    if payment_status["success"]:
                        status = payment_status["status"]
                        amount = payment_status["amount"]
                        
                        # Buscar transação no banco
                        cursor = db.connection.cursor(dictionary=True)
                        cursor.execute("""
                            SELECT * FROM transactions 
                            WHERE payment_id = %s AND type = 'recharge'
                        """, (payment_id,))
                        transaction = cursor.fetchone()
                        
                        if transaction and status == "approved":
                            # Atualizar saldo do usuário
                            db.update_user_balance(transaction["user_id"], amount, "add")
                            
                            # Atualizar status da transação
                            db.update_transaction_status(transaction["id"], "approved")
                            
                            # Log da atividade
                            db.add_log(
                                transaction["user_id"], 
                                "payment_approved", 
                                f"Recarga de R$ {amount} aprovada"
                            )
                            
                            # Processar comissão de afiliado se aplicável
                            self.process_affiliate_commission(transaction["user_id"], amount)
                            
                            return {"success": True, "message": "Pagamento processado"}
                        
                        elif transaction and status in ["rejected", "cancelled"]:
                            # Atualizar status da transação
                            db.update_transaction_status(transaction["id"], status)
                            
                            return {"success": True, "message": "Pagamento rejeitado/cancelado"}
                
            return {"success": False, "error": "Webhook inválido"}
            
        except Exception as e:
            logger.error(f"Erro ao processar webhook: {e}")
            return {"success": False, "error": str(e)}
    
    def process_affiliate_commission(self, user_id, amount):
        """Processa comissão de afiliado"""
        try:
            # Buscar usuário e seu indicador
            user = db.get_user(user_id)
            
            if user and user.get("referrer_id"):
                commission_amount = amount * 0.5  # 50% de comissão
                
                # Adicionar comissão ao saldo do indicador
                db.update_user_balance(user["referrer_id"], commission_amount, "add")
                
                # Criar registro de comissão
                cursor = db.connection.cursor()
                cursor.execute("""
                    INSERT INTO commissions (referrer_id, referred_id, transaction_id, amount, is_paid) 
                    VALUES (%s, %s, (SELECT id FROM transactions WHERE user_id = %s ORDER BY created_at DESC LIMIT 1), %s, TRUE)
                """, (user["referrer_id"], user_id, user_id, commission_amount))
                db.connection.commit()
                
                # Log da comissão
                db.add_log(
                    user["referrer_id"], 
                    "commission_received", 
                    f"Comissão de R$ {commission_amount} por indicação"
                )
                
                return True
                
        except Exception as e:
            logger.error(f"Erro ao processar comissão: {e}")
            return False
    
    def create_purchase_transaction(self, user_id, service_id, amount):
        """Cria transação de compra"""
        try:
            # Verificar saldo do usuário
            user = db.get_user(user_id)
            if not user or user["balance"] < amount:
                return {"success": False, "error": "Saldo insuficiente"}
            
            # Buscar conta disponível
            account = db.get_available_account(service_id)
            if not account:
                return {"success": False, "error": "Produto indisponível"}
            
            # Debitar saldo do usuário
            db.update_user_balance(user_id, amount, "subtract")
            
            # Marcar conta como vendida
            db.mark_account_sold(account["id"], user_id)
            
            # Criar transação
            transaction_id = db.create_transaction(
                user_id=user_id,
                transaction_type='purchase',
                amount=amount,
                description=f"Compra de produto ID: {service_id}",
                service_id=service_id,
                account_id=account["id"]
            )
            
            # Atualizar status da transação
            db.update_transaction_status(transaction_id, "approved")
            
            # Log da compra
            db.add_log(user_id, "purchase_completed", f"Compra de produto ID: {service_id}")
            
            return {
                "success": True,
                "transaction_id": transaction_id,
                "account_data": account["login_data"],
                "service_id": service_id
            }
            
        except Exception as e:
            logger.error(f"Erro na compra: {e}")
            return {"success": False, "error": str(e)}

# Instância global do sistema de pagamento
payment_system = PaymentSystem()