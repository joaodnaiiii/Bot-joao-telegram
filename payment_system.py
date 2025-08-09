import requests
import qrcode
import io
import base64
import uuid
import json
from datetime import datetime, timedelta
import logging
from database import db
import os
from dotenv import load_dotenv

load_dotenv()

class PixPaymentSystem:
    def __init__(self):
        self.access_token = os.getenv('MP_ACCESS_TOKEN')
        self.public_key = os.getenv('MP_PUBLIC_KEY')
        self.base_url = "https://api.mercadopago.com/v1"
        
    def generate_payment_id(self):
        """Gera um ID único para o pagamento"""
        return str(uuid.uuid4())
    
    def create_pix_payment(self, amount, user_id, description="Recarga de saldo"):
        """Cria um pagamento PIX no Mercado Pago"""
        try:
            payment_id = self.generate_payment_id()
            
            # Criar transação no banco
            transaction_id = db.create_transaction(
                user_id=user_id,
                type='recharge',
                amount=amount,
                payment_method='pix'
            )
            
            if not transaction_id:
                return None, "Erro ao criar transação"
            
            # Dados do pagamento
            payment_data = {
                "transaction_amount": float(amount),
                "description": description,
                "payment_method_id": "pix",
                "external_reference": payment_id,
                "notification_url": f"https://your-webhook-url.com/webhook/{payment_id}",
                "payer": {
                    "email": f"user_{user_id}@example.com"
                }
            }
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            # Simular criação do pagamento (substitua pela API real)
            if not self.access_token or self.access_token == "your_mercado_pago_token_here":
                # Modo simulação para demonstração
                qr_code_data = f"00020126580014br.gov.bcb.pix0136{payment_id}520400005303986540{amount:.2f}5802BR5925LOJA VIRTUAL6009SAO PAULO62070503***6304"
                qr_code_img = self.generate_qr_code(qr_code_data)
                
                # Salvar pagamento PIX no banco
                db.create_pix_payment(
                    transaction_id=transaction_id,
                    user_id=user_id,
                    amount=amount,
                    qr_code=qr_code_data,
                    qr_code_base64=qr_code_img,
                    payment_id=payment_id
                )
                
                return {
                    'payment_id': payment_id,
                    'qr_code': qr_code_data,
                    'qr_code_base64': qr_code_img,
                    'amount': amount,
                    'expires_in': 30  # 30 minutos
                }, None
            
            # API real do Mercado Pago
            response = requests.post(
                f"{self.base_url}/payments",
                headers=headers,
                json=payment_data
            )
            
            if response.status_code == 201:
                payment_response = response.json()
                
                # Extrair dados do QR Code
                qr_code_data = payment_response.get('point_of_interaction', {}).get('transaction_data', {}).get('qr_code', '')
                qr_code_img = self.generate_qr_code(qr_code_data)
                
                # Salvar no banco
                db.create_pix_payment(
                    transaction_id=transaction_id,
                    user_id=user_id,
                    amount=amount,
                    qr_code=qr_code_data,
                    qr_code_base64=qr_code_img,
                    payment_id=payment_id
                )
                
                return {
                    'payment_id': payment_id,
                    'mp_payment_id': payment_response.get('id'),
                    'qr_code': qr_code_data,
                    'qr_code_base64': qr_code_img,
                    'amount': amount,
                    'expires_in': 30
                }, None
            else:
                return None, f"Erro na API: {response.text}"
                
        except Exception as e:
            logging.error(f"Erro ao criar pagamento PIX: {e}")
            return None, str(e)
    
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
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return img_str
        except Exception as e:
            logging.error(f"Erro ao gerar QR Code: {e}")
            return None
    
    def check_payment_status(self, payment_id):
        """Verifica o status do pagamento"""
        try:
            pix_payment = db.get_pix_payment(payment_id)
            if not pix_payment:
                return "not_found"
            
            # Simular verificação (substitua pela API real)
            if not self.access_token or self.access_token == "your_mercado_pago_token_here":
                # Para demonstração, simular aprovação após 2 minutos
                created_at = pix_payment[10]  # created_at field
                if datetime.now() - created_at > timedelta(minutes=2):
                    return "approved"
                return "pending"
            
            # API real do Mercado Pago
            headers = {
                "Authorization": f"Bearer {self.access_token}"
            }
            
            # Buscar pagamento na API
            response = requests.get(
                f"{self.base_url}/payments/search",
                headers=headers,
                params={"external_reference": payment_id}
            )
            
            if response.status_code == 200:
                payments = response.json().get('results', [])
                if payments:
                    return payments[0].get('status', 'pending')
            
            return "pending"
            
        except Exception as e:
            logging.error(f"Erro ao verificar pagamento: {e}")
            return "error"
    
    def process_approved_payment(self, payment_id):
        """Processa um pagamento aprovado"""
        try:
            pix_payment = db.get_pix_payment(payment_id)
            if not pix_payment:
                return False, "Pagamento não encontrado"
            
            user_id = pix_payment[2]
            amount = float(pix_payment[3])
            transaction_id = pix_payment[1]
            
            # Atualizar saldo do usuário
            db.update_user_balance(user_id, amount, 'add')
            
            # Atualizar status da transação
            db.update_transaction_status(transaction_id, 'completed', payment_id)
            
            # Atualizar status do PIX
            db.update_pix_status(payment_id, 'approved')
            
            # Processar comissão de afiliado se houver
            user = db.get_user(user_id)
            if user and user[5]:  # referred_by field
                commission = amount * float(os.getenv('COMMISSION_RATE', 0.5))
                db.update_user_balance(user[5], commission, 'add')
                
                # Criar transação de comissão
                db.create_transaction(
                    user_id=user[5],
                    type='commission',
                    amount=commission,
                    payment_method='system'
                )
                db.update_transaction_status(
                    db.create_transaction(user[5], 'commission', commission),
                    'completed'
                )
            
            # Log da atividade
            db.add_log(user_id, "payment_approved", f"PIX aprovado: R$ {amount:.2f}")
            
            return True, f"Pagamento de R$ {amount:.2f} processado com sucesso"
            
        except Exception as e:
            logging.error(f"Erro ao processar pagamento: {e}")
            return False, str(e)
    
    def create_purchase_payment(self, service_id, user_id):
        """Cria um pagamento para compra de serviço"""
        try:
            service = db.get_service(service_id)
            if not service:
                return None, "Serviço não encontrado"
            
            if service[5] <= 0:  # stock field
                return None, "Serviço fora de estoque"
            
            amount = float(service[4])  # price field
            description = f"Compra: {service[2]}"  # name field
            
            payment_id = self.generate_payment_id()
            
            # Criar transação
            transaction_id = db.create_transaction(
                user_id=user_id,
                type='purchase',
                amount=amount,
                service_id=service_id,
                payment_method='pix'
            )
            
            # Gerar QR Code
            qr_code_data = f"00020126580014br.gov.bcb.pix0136{payment_id}520400005303986540{amount:.2f}5802BR5925LOJA VIRTUAL6009SAO PAULO62070503***6304"
            qr_code_img = self.generate_qr_code(qr_code_data)
            
            # Salvar pagamento PIX
            db.create_pix_payment(
                transaction_id=transaction_id,
                user_id=user_id,
                amount=amount,
                qr_code=qr_code_data,
                qr_code_base64=qr_code_img,
                payment_id=payment_id
            )
            
            return {
                'payment_id': payment_id,
                'qr_code': qr_code_data,
                'qr_code_base64': qr_code_img,
                'amount': amount,
                'service_name': service[2],
                'expires_in': 30
            }, None
            
        except Exception as e:
            logging.error(f"Erro ao criar pagamento de compra: {e}")
            return None, str(e)
    
    def process_purchase_payment(self, payment_id):
        """Processa um pagamento de compra aprovado"""
        try:
            pix_payment = db.get_pix_payment(payment_id)
            if not pix_payment:
                return False, "Pagamento não encontrado", None
            
            transaction_id = pix_payment[1]
            user_id = pix_payment[2]
            
            # Buscar transação
            transaction = db.execute_query(
                "SELECT * FROM transactions WHERE id = %s",
                (transaction_id,)
            )[0]
            
            service_id = transaction[4]  # service_id field
            
            # Buscar conta disponível
            account = db.get_available_account(service_id)
            if not account:
                return False, "Serviço fora de estoque", None
            
            # Marcar conta como vendida
            db.sell_account(account[0], user_id)
            
            # Atualizar estoque
            db.update_service_stock(service_id)
            
            # Atualizar status da transação
            db.update_transaction_status(transaction_id, 'completed', payment_id)
            
            # Atualizar status do PIX
            db.update_pix_status(payment_id, 'approved')
            
            # Log da atividade
            service = db.get_service(service_id)
            db.add_log(user_id, "purchase_completed", f"Compra: {service[2]}")
            
            return True, "Compra realizada com sucesso!", {
                'email': account[2],
                'password': account[3],
                'additional_info': account[4],
                'service_name': service[2]
            }
            
        except Exception as e:
            logging.error(f"Erro ao processar compra: {e}")
            return False, str(e), None

# Instância global do sistema de pagamento
pix_system = PixPaymentSystem()