#!/usr/bin/env python3
"""
Bot de Vendas Automatizadas - Sistema Completo
Arquivo principal para executar ambos os bots simultaneamente
"""

import asyncio
import threading
import logging
import signal
import sys
from datetime import datetime

# Importar os bots
from admin_bot import AdminBot
from shop_bot import ShopBot
from sync_system import initialize_sync, shutdown_sync
from database import db

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot_system.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class BotManager:
    def __init__(self):
        self.admin_bot = None
        self.shop_bot = None
        self.admin_thread = None
        self.shop_thread = None
        self.running = False
        
    def start_admin_bot(self):
        """Inicia o bot administrativo em thread separada"""
        try:
            logger.info("Iniciando Bot Administrativo...")
            self.admin_bot = AdminBot()
            self.admin_bot.run()
        except Exception as e:
            logger.error(f"Erro no Bot Administrativo: {e}")
    
    def start_shop_bot(self):
        """Inicia o bot da loja em thread separada"""
        try:
            logger.info("Iniciando Bot da Loja...")
            self.shop_bot = ShopBot()
            self.shop_bot.run()
        except Exception as e:
            logger.error(f"Erro no Bot da Loja: {e}")
    
    def start_system(self):
        """Inicia todo o sistema"""
        try:
            logger.info("🚀 Iniciando Sistema de Vendas Automatizadas...")
            
            # Conectar ao banco de dados
            logger.info("Conectando ao banco de dados...")
            if not db.connect():
                logger.error("❌ Falha ao conectar com o banco de dados!")
                return False
            
            # Criar tabelas se necessário
            logger.info("Verificando estrutura do banco de dados...")
            db.create_tables()
            
            # Inicializar sistema de sincronização
            logger.info("Iniciando sistema de sincronização...")
            initialize_sync()
            
            self.running = True
            
            # Iniciar bot administrativo em thread separada
            logger.info("Iniciando Bot Administrativo...")
            self.admin_thread = threading.Thread(
                target=self.start_admin_bot, 
                name="AdminBot",
                daemon=True
            )
            self.admin_thread.start()
            
            # Aguardar um pouco para o primeiro bot inicializar
            import time
            time.sleep(2)
            
            # Iniciar bot da loja em thread separada
            logger.info("Iniciando Bot da Loja...")
            self.shop_thread = threading.Thread(
                target=self.start_shop_bot, 
                name="ShopBot",
                daemon=True
            )
            self.shop_thread.start()
            
            logger.info("✅ Sistema iniciado com sucesso!")
            logger.info("📊 Bot Administrativo: Ativo")
            logger.info("🛍️ Bot da Loja: Ativo")
            logger.info("🔄 Sistema de Sincronização: Ativo")
            logger.info("🔐 Sistema de Segurança: Ativo")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar sistema: {e}")
            return False
    
    def stop_system(self):
        """Para todo o sistema graciosamente"""
        try:
            logger.info("🛑 Parando sistema...")
            
            self.running = False
            
            # Parar sistema de sincronização
            logger.info("Parando sistema de sincronização...")
            shutdown_sync()
            
            # Parar bots
            if self.admin_bot and self.admin_bot.application:
                logger.info("Parando Bot Administrativo...")
                self.admin_bot.application.stop()
            
            if self.shop_bot and self.shop_bot.application:
                logger.info("Parando Bot da Loja...")
                self.shop_bot.application.stop()
            
            # Desconectar banco de dados
            logger.info("Desconectando banco de dados...")
            db.disconnect()
            
            logger.info("✅ Sistema parado com sucesso!")
            
        except Exception as e:
            logger.error(f"❌ Erro ao parar sistema: {e}")
    
    def wait_for_threads(self):
        """Aguarda as threads terminarem"""
        try:
            while self.running:
                # Verificar se as threads ainda estão vivas
                admin_alive = self.admin_thread and self.admin_thread.is_alive()
                shop_alive = self.shop_thread and self.shop_thread.is_alive()
                
                if not admin_alive and not shop_alive:
                    logger.warning("Ambos os bots pararam inesperadamente")
                    break
                
                # Aguardar um pouco antes de verificar novamente
                import time
                time.sleep(5)
                
        except KeyboardInterrupt:
            logger.info("Interrupção do usuário detectada")
        except Exception as e:
            logger.error(f"Erro no loop principal: {e}")

def signal_handler(signum, frame):
    """Handler para sinais de sistema"""
    logger.info(f"Sinal {signum} recebido, parando sistema...")
    bot_manager.stop_system()
    sys.exit(0)

def print_banner():
    """Exibe banner do sistema"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║    🤖 BOT DE VENDAS AUTOMATIZADAS - SISTEMA COMPLETO        ║
║                                                              ║
║    ✅ Bot Administrativo                                     ║
║    ✅ Bot da Loja                                           ║
║    ✅ Sistema de Pagamentos PIX                             ║
║    ✅ Sistema de Afiliados                                  ║
║    ✅ Sincronização Automática                              ║
║    ✅ Segurança Avançada                                    ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)

def print_status():
    """Exibe status do sistema"""
    status = f"""
📊 STATUS DO SISTEMA - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

🔧 Bot Administrativo:
   • Token: {db.ADMIN_BOT_TOKEN[:10]}...
   • Status: Iniciando...

🛍️ Bot da Loja:
   • Token: {db.SHOP_BOT_TOKEN[:10]}...
   • Status: Iniciando...

💾 Banco de Dados:
   • Host: {db.DB_CONFIG['host']}
   • Database: {db.DB_CONFIG['database']}
   • Status: Conectando...

🔄 Sincronização: Ativa
🔐 Segurança: Ativa
💳 Pagamentos: Mercado Pago

═══════════════════════════════════════════════════════════════

Para parar o sistema: Ctrl+C
Para logs detalhados: tail -f bot_system.log

═══════════════════════════════════════════════════════════════
"""
    print(status)

# Instância global do gerenciador
bot_manager = BotManager()

def main():
    """Função principal"""
    try:
        # Configurar handlers de sinal
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Exibir banner
        print_banner()
        
        # Exibir status
        print_status()
        
        # Iniciar sistema
        if bot_manager.start_system():
            logger.info("Sistema iniciado com sucesso! Pressione Ctrl+C para parar.")
            
            # Aguardar threads
            bot_manager.wait_for_threads()
        else:
            logger.error("Falha ao iniciar sistema!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Interrupção do usuário")
    except Exception as e:
        logger.error(f"Erro crítico: {e}")
        sys.exit(1)
    finally:
        bot_manager.stop_system()

if __name__ == "__main__":
    main()