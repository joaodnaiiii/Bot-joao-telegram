#!/bin/bash

# Bot de Vendas Automatizadas - Script de Instalação
# Este script instala e configura automaticamente o sistema

set -e  # Parar em caso de erro

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para imprimir mensagens coloridas
print_message() {
    echo -e "${2}${1}${NC}"
}

print_banner() {
    clear
    print_message "╔══════════════════════════════════════════════════════════════╗" $BLUE
    print_message "║                                                              ║" $BLUE
    print_message "║    🤖 BOT DE VENDAS AUTOMATIZADAS - INSTALAÇÃO             ║" $BLUE
    print_message "║                                                              ║" $BLUE
    print_message "║    Este script irá instalar e configurar o sistema          ║" $BLUE
    print_message "║    completo de vendas automatizadas via Telegram            ║" $BLUE
    print_message "║                                                              ║" $BLUE
    print_message "╚══════════════════════════════════════════════════════════════╝" $BLUE
    echo
}

# Verificar se está executando como root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_message "⚠️  Não execute este script como root!" $YELLOW
        print_message "Execute como usuário normal. O script pedirá sudo quando necessário." $YELLOW
        exit 1
    fi
}

# Verificar sistema operacional
check_os() {
    print_message "🔍 Verificando sistema operacional..." $BLUE
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command -v apt-get &> /dev/null; then
            OS="ubuntu"
            print_message "✅ Ubuntu/Debian detectado" $GREEN
        elif command -v yum &> /dev/null; then
            OS="centos"
            print_message "✅ CentOS/RHEL detectado" $GREEN
        else
            print_message "❌ Distribuição Linux não suportada" $RED
            exit 1
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        print_message "✅ macOS detectado" $GREEN
    else
        print_message "❌ Sistema operacional não suportado" $RED
        exit 1
    fi
}

# Instalar dependências do sistema
install_system_deps() {
    print_message "📦 Instalando dependências do sistema..." $BLUE
    
    case $OS in
        "ubuntu")
            sudo apt-get update
            sudo apt-get install -y python3 python3-pip python3-venv mysql-server git curl wget
            ;;
        "centos")
            sudo yum update -y
            sudo yum install -y python3 python3-pip mysql-server git curl wget
            ;;
        "macos")
            if ! command -v brew &> /dev/null; then
                print_message "🍺 Instalando Homebrew..." $BLUE
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            fi
            brew install python3 mysql git curl wget
            ;;
    esac
    
    print_message "✅ Dependências do sistema instaladas" $GREEN
}

# Verificar e instalar Python
check_python() {
    print_message "🐍 Verificando Python..." $BLUE
    
    if ! command -v python3 &> /dev/null; then
        print_message "❌ Python 3 não encontrado" $RED
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    REQUIRED_VERSION="3.9"
    
    if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" = "$REQUIRED_VERSION" ]; then
        print_message "✅ Python $PYTHON_VERSION encontrado" $GREEN
    else
        print_message "❌ Python $REQUIRED_VERSION ou superior necessário. Encontrado: $PYTHON_VERSION" $RED
        exit 1
    fi
}

# Criar ambiente virtual
create_venv() {
    print_message "🔧 Criando ambiente virtual Python..." $BLUE
    
    if [ -d "venv" ]; then
        print_message "⚠️  Ambiente virtual já existe. Removendo..." $YELLOW
        rm -rf venv
    fi
    
    python3 -m venv venv
    source venv/bin/activate
    
    print_message "✅ Ambiente virtual criado" $GREEN
}

# Instalar dependências Python
install_python_deps() {
    print_message "📚 Instalando dependências Python..." $BLUE
    
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    print_message "✅ Dependências Python instaladas" $GREEN
}

# Configurar MySQL
setup_mysql() {
    print_message "🗄️  Configurando MySQL..." $BLUE
    
    # Verificar se MySQL está rodando
    if ! systemctl is-active --quiet mysql 2>/dev/null && ! systemctl is-active --quiet mysqld 2>/dev/null; then
        print_message "🚀 Iniciando MySQL..." $BLUE
        case $OS in
            "ubuntu")
                sudo systemctl start mysql
                sudo systemctl enable mysql
                ;;
            "centos")
                sudo systemctl start mysqld
                sudo systemctl enable mysqld
                ;;
            "macos")
                brew services start mysql
                ;;
        esac
    fi
    
    # Criar banco de dados
    print_message "📊 Criando banco de dados..." $BLUE
    echo "Digite a senha do root do MySQL (deixe em branco se não tiver senha):"
    read -s mysql_password
    
    if [ -z "$mysql_password" ]; then
        mysql -u root -e "CREATE DATABASE IF NOT EXISTS vendas_bot CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
    else
        mysql -u root -p$mysql_password -e "CREATE DATABASE IF NOT EXISTS vendas_bot CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
    fi
    
    print_message "✅ Banco de dados configurado" $GREEN
}

# Configurar arquivo de ambiente
setup_env() {
    print_message "⚙️  Configurando variáveis de ambiente..." $BLUE
    
    if [ ! -f ".env" ]; then
        cp .env.example .env
        print_message "📄 Arquivo .env criado a partir do exemplo" $GREEN
    else
        print_message "⚠️  Arquivo .env já existe" $YELLOW
    fi
    
    print_message "📝 Configure o arquivo .env com suas informações:" $YELLOW
    print_message "   - Tokens dos bots do Telegram" $YELLOW
    print_message "   - Credenciais do banco de dados" $YELLOW
    print_message "   - Credenciais do Mercado Pago" $YELLOW
    print_message "   - IDs dos administradores" $YELLOW
    
    read -p "Pressione Enter para continuar após configurar o .env..."
}

# Gerar chave de criptografia
generate_encryption_key() {
    print_message "🔐 Gerando chave de criptografia..." $BLUE
    
    source venv/bin/activate
    python3 -c "
from cryptography.fernet import Fernet
key = Fernet.generate_key()
print('Chave de criptografia gerada:', key.decode())
print('Adicione esta linha ao seu config.py:')
print('ENCRYPTION_KEY =', repr(key))
"
    
    print_message "✅ Chave de criptografia gerada" $GREEN
    read -p "Pressione Enter após adicionar a chave ao config.py..."
}

# Inicializar banco de dados
init_database() {
    print_message "🏗️  Inicializando estrutura do banco de dados..." $BLUE
    
    source venv/bin/activate
    python3 -c "
from database import db
if db.connect():
    db.create_tables()
    print('✅ Tabelas criadas com sucesso!')
else:
    print('❌ Erro ao conectar com o banco de dados')
    exit(1)
"
    
    print_message "✅ Banco de dados inicializado" $GREEN
}

# Criar scripts de inicialização
create_scripts() {
    print_message "📜 Criando scripts de inicialização..." $BLUE
    
    # Script para iniciar o sistema
    cat > start_bots.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python3 main.py
EOF
    chmod +x start_bots.sh
    
    # Script para iniciar apenas o bot admin
    cat > start_admin.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python3 admin_bot.py
EOF
    chmod +x start_admin.sh
    
    # Script para iniciar apenas o bot da loja
    cat > start_shop.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python3 shop_bot.py
EOF
    chmod +x start_shop.sh
    
    # Script para parar os bots
    cat > stop_bots.sh << 'EOF'
#!/bin/bash
pkill -f "python3 main.py"
pkill -f "python3 admin_bot.py"
pkill -f "python3 shop_bot.py"
echo "Bots parados"
EOF
    chmod +x stop_bots.sh
    
    print_message "✅ Scripts criados" $GREEN
}

# Criar serviço systemd (opcional)
create_systemd_service() {
    print_message "🔧 Deseja criar um serviço systemd para iniciar automaticamente? (y/n)" $BLUE
    read -r create_service
    
    if [[ $create_service =~ ^[Yy]$ ]]; then
        CURRENT_DIR=$(pwd)
        USER=$(whoami)
        
        sudo tee /etc/systemd/system/vendas-bot.service > /dev/null << EOF
[Unit]
Description=Bot de Vendas Automatizadas
After=network.target mysql.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$CURRENT_DIR
ExecStart=$CURRENT_DIR/venv/bin/python $CURRENT_DIR/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
        
        sudo systemctl daemon-reload
        sudo systemctl enable vendas-bot.service
        
        print_message "✅ Serviço systemd criado" $GREEN
        print_message "Para iniciar: sudo systemctl start vendas-bot" $BLUE
        print_message "Para parar: sudo systemctl stop vendas-bot" $BLUE
        print_message "Para ver logs: sudo journalctl -u vendas-bot -f" $BLUE
    fi
}

# Teste final
run_tests() {
    print_message "🧪 Executando testes básicos..." $BLUE
    
    source venv/bin/activate
    
    # Testar importações
    python3 -c "
try:
    from database import db
    from payment_system import payment_system
    from security import security_manager
    from sync_system import sync_system
    print('✅ Todas as importações funcionando')
except Exception as e:
    print(f'❌ Erro nas importações: {e}')
    exit(1)
"
    
    # Testar conexão com banco
    python3 -c "
from database import db
if db.connect():
    print('✅ Conexão com banco de dados funcionando')
    db.disconnect()
else:
    print('❌ Erro na conexão com banco de dados')
    exit(1)
"
    
    print_message "✅ Testes básicos passaram" $GREEN
}

# Função principal
main() {
    print_banner
    
    print_message "🚀 Iniciando instalação..." $BLUE
    echo
    
    check_root
    check_os
    install_system_deps
    check_python
    create_venv
    install_python_deps
    setup_mysql
    setup_env
    generate_encryption_key
    init_database
    create_scripts
    create_systemd_service
    run_tests
    
    echo
    print_message "🎉 INSTALAÇÃO CONCLUÍDA COM SUCESSO!" $GREEN
    echo
    print_message "📋 Próximos passos:" $BLUE
    print_message "1. Configure completamente o arquivo .env" $YELLOW
    print_message "2. Configure o arquivo config.py com seus dados" $YELLOW
    print_message "3. Execute: ./start_bots.sh" $YELLOW
    echo
    print_message "📚 Scripts disponíveis:" $BLUE
    print_message "• ./start_bots.sh - Inicia ambos os bots" $YELLOW
    print_message "• ./start_admin.sh - Inicia apenas bot administrativo" $YELLOW
    print_message "• ./start_shop.sh - Inicia apenas bot da loja" $YELLOW
    print_message "• ./stop_bots.sh - Para todos os bots" $YELLOW
    echo
    print_message "📖 Consulte o README.md para documentação completa" $BLUE
    echo
}

# Executar instalação
main "$@"