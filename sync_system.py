import asyncio
import json
import logging
from datetime import datetime, timedelta
from database import db
import threading
import time
from typing import Dict, Any, List
import hashlib

logger = logging.getLogger(__name__)

class SyncSystem:
    def __init__(self):
        self.sync_interval = 60  # Sincronizar a cada 60 segundos
        self.last_sync = {}
        self.sync_running = False
        self.sync_thread = None
        self.data_hashes = {}
        
    def start_sync(self):
        """Inicia o sistema de sincronização em background"""
        if self.sync_running:
            return
        
        self.sync_running = True
        self.sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
        self.sync_thread.start()
        logger.info("Sistema de sincronização iniciado")
    
    def stop_sync(self):
        """Para o sistema de sincronização"""
        self.sync_running = False
        if self.sync_thread:
            self.sync_thread.join()
        logger.info("Sistema de sincronização parado")
    
    def _sync_loop(self):
        """Loop principal de sincronização"""
        while self.sync_running:
            try:
                self.sync_all_data()
                time.sleep(self.sync_interval)
            except Exception as e:
                logger.error(f"Erro no loop de sincronização: {e}")
                time.sleep(30)  # Aguardar antes de tentar novamente
    
    def sync_all_data(self):
        """Sincroniza todos os dados necessários"""
        try:
            # Conectar ao banco se necessário
            if not db.connection or not db.connection.is_connected():
                db.connect()
            
            # Sincronizar diferentes tipos de dados
            self.sync_categories()
            self.sync_services()
            self.sync_stock()
            self.sync_user_balances()
            self.sync_settings()
            
            logger.info("Sincronização completa realizada")
            
        except Exception as e:
            logger.error(f"Erro na sincronização: {e}")
    
    def sync_categories(self):
        """Sincroniza categorias"""
        try:
            cursor = db.connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM categories ORDER BY id")
            categories = cursor.fetchall()
            
            # Calcular hash dos dados
            data_string = json.dumps(categories, default=str, sort_keys=True)
            current_hash = hashlib.md5(data_string.encode()).hexdigest()
            
            # Verificar se houve mudanças
            if self.data_hashes.get('categories') != current_hash:
                self.data_hashes['categories'] = current_hash
                self.last_sync['categories'] = datetime.now()
                logger.debug("Categorias sincronizadas")
                
                # Aqui você pode implementar notificações para outros bots
                self._notify_bots('categories_updated', categories)
            
        except Exception as e:
            logger.error(f"Erro ao sincronizar categorias: {e}")
    
    def sync_services(self):
        """Sincroniza serviços"""
        try:
            cursor = db.connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT s.*, c.name as category_name, c.emoji as category_emoji
                FROM services s
                LEFT JOIN categories c ON s.category_id = c.id
                ORDER BY s.id
            """)
            services = cursor.fetchall()
            
            # Calcular hash dos dados
            data_string = json.dumps(services, default=str, sort_keys=True)
            current_hash = hashlib.md5(data_string.encode()).hexdigest()
            
            # Verificar se houve mudanças
            if self.data_hashes.get('services') != current_hash:
                self.data_hashes['services'] = current_hash
                self.last_sync['services'] = datetime.now()
                logger.debug("Serviços sincronizados")
                
                # Notificar outros bots
                self._notify_bots('services_updated', services)
            
        except Exception as e:
            logger.error(f"Erro ao sincronizar serviços: {e}")
    
    def sync_stock(self):
        """Sincroniza informações de estoque"""
        try:
            cursor = db.connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT 
                    s.id as service_id,
                    s.name as service_name,
                    COUNT(CASE WHEN a.is_sold = FALSE THEN 1 END) as available_stock,
                    COUNT(CASE WHEN a.is_sold = TRUE THEN 1 END) as sold_stock
                FROM services s
                LEFT JOIN accounts a ON s.id = a.service_id
                GROUP BY s.id, s.name
                ORDER BY s.id
            """)
            stock_data = cursor.fetchall()
            
            # Calcular hash dos dados
            data_string = json.dumps(stock_data, default=str, sort_keys=True)
            current_hash = hashlib.md5(data_string.encode()).hexdigest()
            
            # Verificar se houve mudanças
            if self.data_hashes.get('stock') != current_hash:
                self.data_hashes['stock'] = current_hash
                self.last_sync['stock'] = datetime.now()
                logger.debug("Estoque sincronizado")
                
                # Verificar produtos com estoque baixo
                low_stock_services = [s for s in stock_data if s['available_stock'] <= 5 and s['available_stock'] > 0]
                out_of_stock_services = [s for s in stock_data if s['available_stock'] == 0]
                
                if low_stock_services:
                    self._notify_admins_low_stock(low_stock_services)
                
                if out_of_stock_services:
                    self._notify_admins_out_of_stock(out_of_stock_services)
                
                # Notificar outros bots
                self._notify_bots('stock_updated', stock_data)
            
        except Exception as e:
            logger.error(f"Erro ao sincronizar estoque: {e}")
    
    def sync_user_balances(self):
        """Sincroniza saldos dos usuários (apenas estatísticas)"""
        try:
            cursor = db.connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_users,
                    SUM(balance) as total_balance,
                    AVG(balance) as avg_balance,
                    COUNT(CASE WHEN balance > 0 THEN 1 END) as users_with_balance
                FROM users
            """)
            balance_stats = cursor.fetchone()
            
            # Calcular hash dos dados
            data_string = json.dumps(balance_stats, default=str, sort_keys=True)
            current_hash = hashlib.md5(data_string.encode()).hexdigest()
            
            # Verificar se houve mudanças
            if self.data_hashes.get('user_balances') != current_hash:
                self.data_hashes['user_balances'] = current_hash
                self.last_sync['user_balances'] = datetime.now()
                logger.debug("Estatísticas de saldo sincronizadas")
            
        except Exception as e:
            logger.error(f"Erro ao sincronizar saldos: {e}")
    
    def sync_settings(self):
        """Sincroniza configurações do sistema"""
        try:
            cursor = db.connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM settings ORDER BY key_name")
            settings = cursor.fetchall()
            
            # Calcular hash dos dados
            data_string = json.dumps(settings, default=str, sort_keys=True)
            current_hash = hashlib.md5(data_string.encode()).hexdigest()
            
            # Verificar se houve mudanças
            if self.data_hashes.get('settings') != current_hash:
                self.data_hashes['settings'] = current_hash
                self.last_sync['settings'] = datetime.now()
                logger.debug("Configurações sincronizadas")
                
                # Notificar outros bots sobre mudanças de configuração
                self._notify_bots('settings_updated', settings)
            
        except Exception as e:
            logger.error(f"Erro ao sincronizar configurações: {e}")
    
    def _notify_bots(self, event_type: str, data: Any):
        """Notifica outros bots sobre mudanças nos dados"""
        try:
            # Aqui você pode implementar diferentes métodos de notificação:
            # - Redis pub/sub
            # - Webhook HTTP
            # - File system watching
            # - Database triggers
            
            # Por enquanto, apenas logamos a notificação
            logger.info(f"Notificação enviada: {event_type} - {len(data) if isinstance(data, list) else 'N/A'} itens")
            
            # Exemplo de implementação com arquivo (para desenvolvimento):
            notification = {
                'timestamp': datetime.now().isoformat(),
                'event_type': event_type,
                'data': data
            }
            
            # Salvar em arquivo de notificação (opcional)
            try:
                with open('/tmp/bot_notifications.json', 'w') as f:
                    json.dump(notification, f, default=str, indent=2)
            except:
                pass  # Ignorar erros de arquivo
                
        except Exception as e:
            logger.error(f"Erro ao notificar bots: {e}")
    
    def _notify_admins_low_stock(self, low_stock_services: List[Dict]):
        """Notifica administradores sobre estoque baixo"""
        try:
            from config import ADMIN_IDS
            
            message = "⚠️ **Alerta de Estoque Baixo**\n\nOs seguintes produtos estão com estoque baixo:\n\n"
            
            for service in low_stock_services:
                message += f"• {service['service_name']}: {service['available_stock']} restantes\n"
            
            # Registrar log para notificação
            db.add_log(None, "low_stock_alert", f"Estoque baixo em {len(low_stock_services)} produtos")
            
            # Aqui você implementaria o envio real da notificação
            logger.warning(f"Estoque baixo detectado em {len(low_stock_services)} produtos")
            
        except Exception as e:
            logger.error(f"Erro ao notificar estoque baixo: {e}")
    
    def _notify_admins_out_of_stock(self, out_of_stock_services: List[Dict]):
        """Notifica administradores sobre produtos sem estoque"""
        try:
            message = "🔴 **Alerta de Estoque Esgotado**\n\nOs seguintes produtos estão sem estoque:\n\n"
            
            for service in out_of_stock_services:
                message += f"• {service['service_name']}\n"
            
            # Registrar log para notificação
            db.add_log(None, "out_of_stock_alert", f"Estoque esgotado em {len(out_of_stock_services)} produtos")
            
            # Aqui você implementaria o envio real da notificação
            logger.error(f"Produtos sem estoque: {len(out_of_stock_services)}")
            
        except Exception as e:
            logger.error(f"Erro ao notificar estoque esgotado: {e}")
    
    def force_sync(self):
        """Força uma sincronização imediata"""
        try:
            logger.info("Forçando sincronização...")
            self.sync_all_data()
            return True
        except Exception as e:
            logger.error(f"Erro na sincronização forçada: {e}")
            return False
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Retorna status da sincronização"""
        return {
            'running': self.sync_running,
            'last_sync': self.last_sync,
            'data_hashes': self.data_hashes,
            'sync_interval': self.sync_interval
        }
    
    def update_sync_interval(self, new_interval: int):
        """Atualiza intervalo de sincronização"""
        if new_interval >= 30:  # Mínimo de 30 segundos
            self.sync_interval = new_interval
            logger.info(f"Intervalo de sincronização atualizado para {new_interval} segundos")
            return True
        return False

class CacheManager:
    """Gerenciador de cache para dados sincronizados"""
    
    def __init__(self):
        self.cache = {}
        self.cache_timestamps = {}
        self.cache_ttl = 300  # 5 minutos
    
    def get(self, key: str) -> Any:
        """Busca item do cache"""
        if key in self.cache:
            # Verificar se não expirou
            if datetime.now().timestamp() - self.cache_timestamps[key] < self.cache_ttl:
                return self.cache[key]
            else:
                # Remover item expirado
                del self.cache[key]
                del self.cache_timestamps[key]
        return None
    
    def set(self, key: str, value: Any):
        """Define item no cache"""
        self.cache[key] = value
        self.cache_timestamps[key] = datetime.now().timestamp()
    
    def clear(self, key: str = None):
        """Limpa cache"""
        if key:
            self.cache.pop(key, None)
            self.cache_timestamps.pop(key, None)
        else:
            self.cache.clear()
            self.cache_timestamps.clear()
    
    def get_cached_categories(self):
        """Busca categorias do cache ou banco"""
        categories = self.get('categories')
        if categories is None:
            categories = db.get_categories()
            self.set('categories', categories)
        return categories
    
    def get_cached_services(self, category_id: int):
        """Busca serviços do cache ou banco"""
        cache_key = f'services_{category_id}'
        services = self.get(cache_key)
        if services is None:
            services = db.get_services_by_category(category_id)
            self.set(cache_key, services)
        return services

# Instâncias globais
sync_system = SyncSystem()
cache_manager = CacheManager()

# Função para inicializar o sistema de sincronização
def initialize_sync():
    """Inicializa o sistema de sincronização"""
    try:
        sync_system.start_sync()
        logger.info("Sistema de sincronização inicializado com sucesso")
        return True
    except Exception as e:
        logger.error(f"Erro ao inicializar sincronização: {e}")
        return False

# Função para parar o sistema de sincronização
def shutdown_sync():
    """Para o sistema de sincronização"""
    try:
        sync_system.stop_sync()
        logger.info("Sistema de sincronização finalizado")
        return True
    except Exception as e:
        logger.error(f"Erro ao finalizar sincronização: {e}")
        return False