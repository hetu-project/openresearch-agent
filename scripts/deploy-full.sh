#!/bin/bash

# AI Agent Deployment Script
# Used to deploy openresearch-agent service

set -e  # Exit immediately if a command exits with a non-zero status

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Log functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Get absolute path of script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
AI_AGENT_DIR="$PROJECT_ROOT/ai-agent"
MCP_SERVER_DIR="$PROJECT_ROOT/../openresearch-mcp-server"

# Configuration variables
SERVICE_NAME="ai-agent"
SERVICE_USER="ai-agent"
SERVICE_PORT="${PORT:-8000}"
SERVICE_HOST="${HOST:-0.0.0.0}"
ENVIRONMENT="${ENVIRONMENT:-production}"
PYTHON_VERSION="${PYTHON_VERSION:-3.11}"

# Display deployment information
show_deploy_info() {
    log_info "=== AI Agent Deployment Info ==="
    log_info "Project Root: $PROJECT_ROOT"
    log_info "AI Agent Directory: $AI_AGENT_DIR"
    log_info "MCP Server Directory: $MCP_SERVER_DIR"
    log_info "Service Name: $SERVICE_NAME"
    log_info "Service Port: $SERVICE_PORT"
    log_info "Service Host: $SERVICE_HOST"
    log_info "Environment: $ENVIRONMENT"
    log_info "Python Version: $PYTHON_VERSION"
    log_info "=========================="
}

# Check system dependencies
check_system_dependencies() {
    log_info "Checking system dependencies..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 is not installed"
        exit 1
    fi
    
    # Check pip
    if ! command -v pip3 &> /dev/null; then
        log_error "pip3 is not installed"
        exit 1
    fi
    
    # Check systemd (for service management)
    if ! command -v systemctl &> /dev/null; then
        log_warning "systemctl is not available, service installation will be skipped"
    fi
    
    log_success "System dependency check completed"
}

# Check project structure
check_project_structure() {
    log_info "Checking project structure..."
    
    # Check AI Agent directory
    if [ ! -d "$AI_AGENT_DIR" ]; then
        log_error "AI Agent directory does not exist: $AI_AGENT_DIR"
        exit 1
    fi
    
    # Check main file
    if [ ! -f "$AI_AGENT_DIR/main.py" ]; then
        log_error "Main file does not exist: $AI_AGENT_DIR/main.py"
        exit 1
    fi
    
    # Check configuration file
    if [ ! -f "$AI_AGENT_DIR/configs/settings.py" ]; then
        log_error "Configuration file does not exist: $AI_AGENT_DIR/configs/settings.py"
        exit 1
    fi
    
    # Check environment variable file (in project root)
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        log_warning "Environment variable file does not exist: $PROJECT_ROOT/.env"
    fi
    
    # Check MCP server directory
    if [ ! -d "$MCP_SERVER_DIR" ]; then
        log_warning "MCP server directory does not exist: $MCP_SERVER_DIR"
        log_warning "Please ensure openresearch-mcp-server project is in the correct location"
    fi
    
    log_success "Project structure check completed"
}

# Create service user
create_service_user() {
    if [ "$ENVIRONMENT" = "production" ]; then
        log_info "Creating service user..."
        
        if ! id "$SERVICE_USER" &>/dev/null; then
            sudo useradd --system --shell /bin/false --home-dir /nonexistent --no-create-home "$SERVICE_USER"
            log_success "Service user $SERVICE_USER created successfully"
        else
            log_info "Service user $SERVICE_USER already exists"
        fi
    fi
}

# Set up Python virtual environment
setup_virtual_environment() {
    log_info "Setting up Python virtual environment..."
    
    cd "$AI_AGENT_DIR"
    
    # Create virtual environment
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        log_success "Virtual environment created successfully"
    else
        log_info "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install dependencies
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        log_success "Dependencies installation completed"
    else
        log_warning "requirements.txt does not exist, skipping dependency installation"
    fi
    
    deactivate
}

# Set up MCP server environment
setup_mcp_server() {
    if [ -d "$MCP_SERVER_DIR" ]; then
        log_info "Setting up MCP server environment..."
        
        cd "$MCP_SERVER_DIR"
        
        # Create MCP server virtual environment
        if [ ! -d "venv" ]; then
            python3 -m venv venv
            log_success "MCP server virtual environment created successfully"
        else
            log_info "MCP server virtual environment already exists"
        fi
        
        # Activate virtual environment and install dependencies
        source venv/bin/activate
        pip install --upgrade pip
        
        if [ -f "requirements.txt" ]; then
            pip install -r requirements.txt
            log_success "MCP server dependencies installation completed"
        fi
        
        deactivate
        cd "$AI_AGENT_DIR"
    else
        log_warning "Skipping MCP server setup"
    fi
}

# Handle environment variable file
setup_environment_file() {
    log_info "Processing environment variable file..."
    
    # Check .env file in project root
    if [ -f "$PROJECT_ROOT/.env" ]; then
        log_info "Found .env file in project root"
        
        # If production environment, copy and modify configuration
        if [ "$ENVIRONMENT" = "production" ]; then
            # Create production environment configuration
            cp "$PROJECT_ROOT/.env" "$PROJECT_ROOT/.env.production"
            
            # Modify production-specific configuration
            sed -i.bak "s/DEBUG=true/DEBUG=false/g" "$PROJECT_ROOT/.env.production"
            sed -i.bak "s/LOG_LEVEL=DEBUG/LOG_LEVEL=INFO/g" "$PROJECT_ROOT/.env.production"
            sed -i.bak "s/HOST=localhost/HOST=$SERVICE_HOST/g" "$PROJECT_ROOT/.env.production"
            sed -i.bak "s/PORT=8000/PORT=$SERVICE_PORT/g" "$PROJECT_ROOT/.env.production"
            
            # Database configuration - usually enabled in production
            sed -i.bak "s/DB_SKIP_IN_DEV=true/DB_SKIP_IN_DEV=false/g" "$PROJECT_ROOT/.env.production"
            
            # Clean up backup files
            rm -f "$PROJECT_ROOT/.env.production.bak"
            
            log_success "Production environment configuration file created"
        fi
    else
        log_warning ".env file does not exist, creating default configuration"
        create_default_env_file
    fi
}

# Create default environment variable file
create_default_env_file() {
    log_info "Creating default environment variable file..."
    
    cat > "$PROJECT_ROOT/.env" << EOF
# AI Agent Configuration
APP_NAME=AI-Agent
APP_VERSION=1.0.0
DEBUG=${DEBUG:-false}
LOG_LEVEL=${LOG_LEVEL:-INFO}

# Server Configuration
HOST=$SERVICE_HOST
PORT=$SERVICE_PORT

# LLM Configuration - Together.ai
LLM_PROVIDER=together
TOGETHER_API_KEY=${TOGETHER_API_KEY:-}
TOGETHER_MODEL=Qwen/Qwen2.5-VL-72B-Instruct
TOGETHER_BASE_URL=https://api.together.xyz/v1/chat/completions
LLM_MAX_TOKENS=2000
LLM_TEMPERATURE=0.7
LLM_TIMEOUT=30

# MCP Server Configuration
MCP_SERVER_HOST=localhost
MCP_SERVER_PORT=8001
MCP_SERVER_TIMEOUT=60
MCP_ENABLE_DEBUG_LOG=true
MCP_DEBUG_LOG_FILE=ai-agent/logs/mcp_debug.log

# MCP Configuration - stdio protocol
MCP_COMMAND=../openresearch-mcp-server/venv/bin/python
MCP_ARGS=["../openresearch-mcp-server/src/main.py"]
MCP_CWD=../openresearch-mcp-server
MCP_TIMEOUT=30
MCP_MAX_RETRIES=3
MCP_RETRY_DELAY=1.0

# Database Configuration
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}
DB_NAME=${DB_NAME:-openrearch}
DB_USER=${DB_USER:-postgres}
DB_PASSWORD=${DB_PASSWORD:-123456}
DATABASE_URL=postgresql://\${DB_USER}:\${DB_PASSWORD}@\${DB_HOST}:\${DB_PORT}/\${DB_NAME}

# Database Control - Database enabled by default in production
DB_SKIP_IN_DEV=${DB_SKIP_IN_DEV:-false}

# Cache Configuration
CACHE_TYPE=memory
CACHE_TTL=3600
EOF
    log_success "Default .env file created"
}

# Create log directory
setup_logging() {
    log_info "Setting up log directory..."
    
    # Create log directory
    mkdir -p "$AI_AGENT_DIR/logs"
    
    # Set log directory permissions
    if [ "$ENVIRONMENT" = "production" ]; then
        sudo chown -R "$SERVICE_USER:$SERVICE_USER" "$AI_AGENT_DIR/logs"
        sudo chmod -R 755 "$AI_AGENT_DIR/logs"
    else
        chmod -R 755 "$AI_AGENT_DIR/logs"
    fi
    
    log_success "Log directory setup completed"
}

# Set file permissions
setup_permissions() {
    log_info "Setting file permissions..."
    
    if [ "$ENVIRONMENT" = "production" ]; then
        # Production environment permissions
        sudo chown -R "$SERVICE_USER:$SERVICE_USER" "$AI_AGENT_DIR"
        sudo chown "$SERVICE_USER:$SERVICE_USER" "$PROJECT_ROOT/.env"*
        sudo chmod -R 755 "$AI_AGENT_DIR"
        sudo chmod 644 "$PROJECT_ROOT/.env"*
        sudo chmod +x "$AI_AGENT_DIR/main.py"
    else
        # Development environment permissions
        chmod -R 755 "$AI_AGENT_DIR"
        chmod +x "$AI_AGENT_DIR/main.py"
        chmod 644 "$PROJECT_ROOT/.env"*
    fi
    
    log_success "File permissions setup completed"
}

# Create systemd service file
create_systemd_service() {
    if [ "$ENVIRONMENT" = "production" ] && command -v systemctl &> /dev/null; then
        log_info "Creating systemd service..."
        
        # Determine environment file to use
        ENV_FILE="$PROJECT_ROOT/.env.production"
        if [ ! -f "$ENV_FILE" ]; then
            ENV_FILE="$PROJECT_ROOT/.env"
        fi
        
        sudo tee /etc/systemd/system/${SERVICE_NAME}.service > /dev/null << EOF
[Unit]
Description=AI Agent Service
After=network.target
Wants=network.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$AI_AGENT_DIR
Environment=PATH=$AI_AGENT_DIR/venv/bin
EnvironmentFile=$ENV_FILE
ExecStart=$AI_AGENT_DIR/venv/bin/python $AI_AGENT_DIR/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=$SERVICE_NAME

# Security Settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$AI_AGENT_DIR/logs
ReadWritePaths=$PROJECT_ROOT

[Install]
WantedBy=multi-user.target
EOF
        
        # Reload systemd
        sudo systemctl daemon-reload
        sudo systemctl enable "$SERVICE_NAME"
        
        log_success "systemd service creation completed"
    else
        log_info "Skipping systemd service creation"
    fi
}

# Start service
start_service() {
    log_info "Starting service..."
    
    if [ "$ENVIRONMENT" = "production" ] && command -v systemctl &> /dev/null; then
        # Production environment uses systemd
        sudo systemctl start "$SERVICE_NAME"
        sleep 3
        sudo systemctl status "$SERVICE_NAME" --no-pager
        log_success "Service startup completed"
    else
        # Development environment runs directly
        log_info "Development mode, please start service manually:"
        log_info "cd $AI_AGENT_DIR"
        log_info "source venv/bin/activate"
        log_info "python main.py"
    fi
}

# Verify deployment
verify_deployment() {
    log_info "Verifying deployment..."
    
    # Wait for service to start
    sleep 5
    
    # Check if port is listening
    if command -v netstat &> /dev/null; then
        if netstat -tuln | grep ":$SERVICE_PORT " > /dev/null; then
            log_success "Service port $SERVICE_PORT is listening"
        else
            log_warning "Service port $SERVICE_PORT is not listening"
        fi
    fi
    
    # Check HTTP response
    if command -v curl &> /dev/null; then
        if curl -s "http://localhost:$SERVICE_PORT/" > /dev/null; then
            log_success "HTTP service response is normal"
        else
            log_warning "HTTP service is not responding"
        fi
    fi
}

# Show deployment result
show_deployment_result() {
    log_success "=== Deployment Complete ==="
    log_info "Service Address: http://$SERVICE_HOST:$SERVICE_PORT"
    log_info "API Documentation: http://$SERVICE_HOST:$SERVICE_PORT/docs"
    log_info "Health Check: http://$SERVICE_HOST:$SERVICE_PORT/api/v1/health"
    
    if [ "$ENVIRONMENT" = "production" ]; then
        log_info ""
        log_info "Service Management Commands:"
        log_info "  Start Service: sudo systemctl start $SERVICE_NAME"
        log_info "  Stop Service: sudo systemctl stop $SERVICE_NAME"
        log_info "  Restart Service: sudo systemctl restart $SERVICE_NAME"
        log_info "  Check Status: sudo systemctl status $SERVICE_NAME"
        log_info "  View Logs: sudo journalctl -u $SERVICE_NAME -f"
    fi
    
    log_info ""
    log_info "Configuration Files:"
    log_info "  Environment Variables: $PROJECT_ROOT/.env"
    if [ -f "$PROJECT_ROOT/.env.production" ]; then
        log_info "  Production Config: $PROJECT_ROOT/.env.production"
    fi
    
    log_info ""
    log_info "Log Files:"
    log_info "  Application Log: $AI_AGENT_DIR/logs/app.log"
    log_info "  MCP Log: $AI_AGENT_DIR/logs/mcp_debug.log"
    
    if [ "$ENVIRONMENT" = "production" ]; then
        log_info "  System Log: sudo journalctl -u $SERVICE_NAME"
    fi
    
    log_success "=================="
}

# Database Setup Information
show_database_info() {
    log_info ""
    log_info "=== Database Configuration Guide ==="
    log_info "Current database configuration may need to be adjusted based on actual environment:"
    log_info ""
    log_info "Environment Variables:"
    log_info "  DB_HOST - Database Host Address"
    log_info "  DB_PORT - Database Port (default: 5432)"
    log_info "  DB_NAME - Database Name"
    log_info "  DB_USER - Database Username"
    log_info "  DB_PASSWORD - Database Password"
    log_info "  DB_SKIP_IN_DEV - Skip Database in Development (true/false)"
    log_info ""
    log_info "To modify database configuration, please edit:"
    if [ "$ENVIRONMENT" = "production" ] && [ -f "$PROJECT_ROOT/.env.production" ]; then
        log_info "  $PROJECT_ROOT/.env.production"
    else
        log_info "  $PROJECT_ROOT/.env"
    fi
    log_info ""
    log_info "Database Initialization:"
    log_info "  cd $AI_AGENT_DIR"
    log_info "  python data/init_db.py"
    log_info "=========================="
}

# Main Function
main() {
    log_info "Starting AI Agent Service Deployment..."
    
    show_deploy_info
    check_system_dependencies
    check_project_structure
    create_service_user
    setup_virtual_environment
    setup_mcp_server
    setup_environment_file
    setup_logging
    setup_permissions
    create_systemd_service
    start_service
    verify_deployment
    show_deployment_result
    show_database_info
    
    log_success "AI Agent Deployment Complete!"
}

# Cleanup Function
cleanup() {
    log_info "Performing cleanup..."
    
    if [ "$ENVIRONMENT" = "production" ] && command -v systemctl &> /dev/null; then
        if systemctl is-active --quiet "$SERVICE_NAME"; then
            sudo systemctl stop "$SERVICE_NAME"
            log_info "Service stopped"
        fi
    fi
}

# Help Information
show_help() {
    echo "AI Agent Deployment Script"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -h, --help          Show help information"
    echo "  -e, --env ENV       Set deployment environment (development|production, default: production)"
    echo "  -p, --port PORT     Set service port (default: 8000)"
    echo "  -H, --host HOST     Set service host (default: 0.0.0.0)"
    echo "  --cleanup           Clean up service"
    echo ""
    echo "Environment Variables:"
    echo "  ENVIRONMENT         Deployment Environment"
    echo "  PORT               Service Port"
    echo "  HOST               Service Host"
    echo "  DB_HOST            Database Host"
    echo "  DB_PORT            Database Port"
    echo "  DB_NAME            Database Name"
    echo "  DB_USER            Database User"
    echo "  DB_PASSWORD        Database Password"
    echo "  TOGETHER_API_KEY   Together.ai API Key"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Production deployment"
    echo "  $0 -e development                    # Development deployment"
    echo "  $0 -p 8080 -H 127.0.0.1             # Specify port and host"
    echo "  $0 --cleanup                         # Clean up service"
}

# Parse Command Line Arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -e|--env)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -p|--port)
            SERVICE_PORT="$2"
            shift 2
            ;;
        -H|--host)
            SERVICE_HOST="$2"
            shift 2
            ;;
        --cleanup)
            cleanup
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Set Error Handler
trap cleanup EXIT

# Execute Main Function
main