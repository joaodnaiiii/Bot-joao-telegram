import qrcode
import io
import base64
import json
import requests
from datetime import datetime, timedelta
import config
import hashlib
import uuid

class PixPayment:
    def __init__(self):
        self.pix_key = config.PIX_KEY
        
    def generate_qr_code(self, amount, user_id, description="Recarga de saldo"):
        """Generate PIX QR Code for payment"""
        try:
            # Generate unique transaction ID
            transaction_id = str(uuid.uuid4())[:8]
            
            # Create PIX payload (simplified version)
            payload = self._create_pix_payload(amount, description, transaction_id)
            
            # Generate QR Code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(payload)
            qr.make(fit=True)
            
            # Create image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return {
                'qr_code': img_str,
                'payload': payload,
                'transaction_id': transaction_id,
                'expires_at': datetime.utcnow() + timedelta(minutes=30)
            }
            
        except Exception as e:
            print(f"Error generating QR code: {e}")
            return None
    
    def _create_pix_payload(self, amount, description, transaction_id):
        """Create PIX payload string"""
        # Simplified PIX payload format
        payload_format = "01"  # Payload Format Indicator
        merchant_info = "0014BR.GOV.BCB.PIX"  # Merchant Account Information
        merchant_category = "5204"  # Merchant Category Code
        currency = "5303986"  # Transaction Currency (986 = BRL)
        amount_str = f"54{len(str(amount)):02d}{amount:.2f}"
        country_code = "5802BR"  # Country Code
        merchant_name = f"59{len('JOAZINHO STORE'):02d}JOAZINHO STORE"
        merchant_city = f"60{len('SAO PAULO'):02d}SAO PAULO"
        
        # PIX Key
        pix_key_info = f"0014BR.GOV.BCB.PIX01{len(self.pix_key):02d}{self.pix_key}"
        
        # Additional Data
        additional_data = f"62{len(transaction_id) + 4:02d}05{len(transaction_id):02d}{transaction_id}"
        
        # Combine all parts
        payload = (
            f"{payload_format}01{merchant_info}{merchant_category}0000{currency}"
            f"{amount_str}{country_code}{merchant_name}{merchant_city}"
            f"26{len(pix_key_info):02d}{pix_key_info}{additional_data}6304"
        )
        
        # Calculate CRC16
        crc = self._calculate_crc16(payload)
        payload += crc
        
        return payload
    
    def _calculate_crc16(self, data):
        """Calculate CRC16 for PIX payload"""
        crc = 0xFFFF
        for byte in data.encode('utf-8'):
            crc ^= byte << 8
            for _ in range(8):
                if crc & 0x8000:
                    crc = (crc << 1) ^ 0x1021
                else:
                    crc <<= 1
                crc &= 0xFFFF
        return f"{crc:04X}"
    
    def verify_payment(self, transaction_id):
        """Verify if payment was received (mock implementation)"""
        # In a real implementation, this would check with your payment provider
        # For now, we'll simulate payment verification
        # You would integrate with Mercado Pago, Gerencianet, etc.
        return False
    
    def simulate_payment_webhook(self, transaction_id, amount, user_id):
        """Simulate payment webhook for testing"""
        # This would be called by your payment provider's webhook
        from database import SessionLocal, User, Recharge
        
        db = SessionLocal()
        try:
            # Find the recharge record
            recharge = db.query(Recharge).filter(
                Recharge.payment_id == transaction_id,
                Recharge.status == 'pending'
            ).first()
            
            if recharge:
                # Update recharge status
                recharge.status = 'completed'
                recharge.completed_at = datetime.utcnow()
                
                # Update user balance
                user = db.query(User).filter(User.id == recharge.user_id).first()
                if user:
                    user.balance += amount
                    
                    # Process affiliate commission if user has referrer
                    if user.referrer_id:
                        referrer = db.query(User).filter(User.id == user.referrer_id).first()
                        if referrer:
                            commission = amount * config.AFFILIATE_COMMISSION_RATE
                            referrer.balance += commission
                
                db.commit()
                return True
                
        except Exception as e:
            print(f"Error processing payment: {e}")
            db.rollback()
        finally:
            db.close()
            
        return False

class MercadoPagoIntegration:
    """Integration with Mercado Pago API for real PIX payments"""
    
    def __init__(self):
        self.access_token = config.MERCADOPAGO_ACCESS_TOKEN
        self.base_url = "https://api.mercadopago.com/v1"
    
    def create_payment(self, amount, user_id, description="Recarga de saldo"):
        """Create a PIX payment with Mercado Pago"""
        if not self.access_token:
            return None
            
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        payment_data = {
            "transaction_amount": amount,
            "description": description,
            "payment_method_id": "pix",
            "payer": {
                "email": f"user{user_id}@example.com"
            },
            "notification_url": f"{config.WEBHOOK_URL}/webhook/mercadopago"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/payments",
                headers=headers,
                json=payment_data
            )
            
            if response.status_code == 201:
                payment_info = response.json()
                return {
                    'payment_id': payment_info['id'],
                    'qr_code': payment_info['point_of_interaction']['transaction_data']['qr_code'],
                    'qr_code_base64': payment_info['point_of_interaction']['transaction_data']['qr_code_base64'],
                    'expires_at': datetime.utcnow() + timedelta(minutes=30)
                }
        except Exception as e:
            print(f"Error creating Mercado Pago payment: {e}")
        
        return None
    
    def get_payment_status(self, payment_id):
        """Get payment status from Mercado Pago"""
        if not self.access_token:
            return None
            
        headers = {
            'Authorization': f'Bearer {self.access_token}'
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/payments/{payment_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Error getting payment status: {e}")
        
        return None