#!/bin/bash

# 小微企业大模型交互管理系统 - Ubuntu 24.04 部署脚本（DeepSeek API版本）
# 使用方法：chmod +x deploy_ubuntu_deepseek.sh && sudo ./deploy_ubuntu_deepseek.sh

set -e

echo "======================================"
echo "小微企业大模型交互管理系统部署脚本"
echo "版本：DeepSeek API 集成版"
echo "目标系统：Ubuntu 24.04"
echo "======================================"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
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

# 检查是否为root用户
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "此脚本需要root权限运行"
        log_info "请使用: sudo $0"
        exit 1
    fi
}

# 更新系统
update_system() {
    log_info "更新系统包..."
    apt update && apt upgrade -y
    log_success "系统更新完成"
}

# 安装基础依赖
install_dependencies() {
    log_info "安装基础依赖..."
    apt install -y \
        python3 \
        python3-pip \
        python3-venv \
        nginx \
        git \
        curl \
        wget \
        unzip \
        sqlite3 \
        build-essential \
        python3-dev \
        libffi-dev \
        libssl-dev \
        portaudio19-dev \
        python3-pyaudio \
        ufw
    
    log_success "基础依赖安装完成"
}

# 创建应用用户
create_app_user() {
    log_info "创建应用用户..."
    if ! id "enterprise" &>/dev/null; then
        useradd -m -s /bin/bash enterprise
        log_success "用户 enterprise 创建成功"
    else
        log_warning "用户 enterprise 已存在"
    fi
}

# 创建应用目录
create_directories() {
    log_info "创建应用目录..."
    
    APP_DIR="/opt/enterprise-system"
    mkdir -p $APP_DIR
    mkdir -p $APP_DIR/logs
    mkdir -p $APP_DIR/uploads
    mkdir -p $APP_DIR/backups
    mkdir -p $APP_DIR/data
    
    # 设置目录权限
    chown -R enterprise:enterprise $APP_DIR
    chmod -R 755 $APP_DIR
    
    log_success "应用目录创建完成: $APP_DIR"
}

# 复制应用代码
copy_application() {
    log_info "复制应用代码..."
    
    APP_DIR="/opt/enterprise-system"
    CURRENT_DIR=$(pwd)
    
    # 复制后端代码
    cp -r $CURRENT_DIR/backend $APP_DIR/
    cp -r $CURRENT_DIR/frontend $APP_DIR/
    
    # 复制配置文件
    if [ -f "$CURRENT_DIR/# 数据库配置.txt" ]; then
        cp "$CURRENT_DIR/# 数据库配置.txt" $APP_DIR/
    fi
    
    # 复制文档
    if [ -f "$CURRENT_DIR/DeepSeek_API_配置说明.md" ]; then
        cp "$CURRENT_DIR/DeepSeek_API_配置说明.md" $APP_DIR/
    fi
    
    # 设置权限
    chown -R enterprise:enterprise $APP_DIR
    
    log_success "应用代码复制完成"
}

# 创建Python虚拟环境
create_venv() {
    log_info "创建Python虚拟环境..."
    
    APP_DIR="/opt/enterprise-system"
    cd $APP_DIR
    
    # 以enterprise用户身份创建虚拟环境
    sudo -u enterprise python3 -m venv venv
    
    log_success "Python虚拟环境创建完成"
}

# 安装Python依赖
install_python_deps() {
    log_info "安装Python依赖..."
    
    APP_DIR="/opt/enterprise-system"
    cd $APP_DIR
    
    # 激活虚拟环境并安装依赖
    sudo -u enterprise bash -c "
        source venv/bin/activate
        pip install --upgrade pip
        pip install -r backend/requirements.txt
    "
    
    log_success "Python依赖安装完成"
}

# 配置数据库
setup_database() {
    log_info "配置SQLite数据库..."
    
    APP_DIR="/opt/enterprise-system"
    cd $APP_DIR
    
    # 创建数据库文件
    sudo -u enterprise touch data/enterprise.db
    sudo -u enterprise chmod 664 data/enterprise.db
    
    # 初始化数据库
    sudo -u enterprise bash -c "
        source venv/bin/activate
        cd backend
        python init_db.py
    "
    
    log_success "数据库配置完成"
}

# 创建配置文件
create_config() {
    log_info "创建配置文件..."
    
    APP_DIR="/opt/enterprise-system"
    
    # 创建环境变量文件
    cat > $APP_DIR/.env << EOF
# DeepSeek API 配置
DEEPSEEK_API_KEY=your-deepseek-api-key-here

# 数据库配置
DATABASE_URL=sqlite:///data/enterprise.db

# 安全配置
SECRET_KEY=$(openssl rand -hex 32)
AES_KEY=$(openssl rand -hex 16)

# 应用配置
DEBUG=false
HOST=127.0.0.1
PORT=8000
EOF

    chown enterprise:enterprise $APP_DIR/.env
    chmod 600 $APP_DIR/.env
    
    log_success "配置文件创建完成"
    log_warning "请编辑 $APP_DIR/.env 文件，设置您的 DeepSeek API 密钥"
}

# 创建systemd服务
create_systemd_service() {
    log_info "创建systemd服务..."
    
    cat > /etc/systemd/system/enterprise-system.service << EOF
[Unit]
Description=Enterprise Management System
After=network.target

[Service]
Type=simple
User=enterprise
Group=enterprise
WorkingDirectory=/opt/enterprise-system/backend
Environment=PATH=/opt/enterprise-system/venv/bin
EnvironmentFile=/opt/enterprise-system/.env
ExecStart=/opt/enterprise-system/venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable enterprise-system
    
    log_success "systemd服务创建完成"
}

# 配置Nginx
configure_nginx() {
    log_info "配置Nginx..."
    
    # 备份默认配置
    if [ -f /etc/nginx/sites-available/default ]; then
        cp /etc/nginx/sites-available/default /etc/nginx/sites-available/default.backup
    fi
    
    # 创建新的配置文件
    cat > /etc/nginx/sites-available/enterprise-system << EOF
server {
    listen 80;
    server_name _;
    
    # 前端静态文件
    location / {
        root /opt/enterprise-system/frontend;
        index index.html;
        try_files \$uri \$uri/ /index.html;
    }
    
    # API代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # 文件上传大小限制
    client_max_body_size 50M;
    
    # Gzip压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
}
EOF

    # 启用站点
    ln -sf /etc/nginx/sites-available/enterprise-system /etc/nginx/sites-enabled/
    
    # 删除默认站点
    rm -f /etc/nginx/sites-enabled/default
    
    # 测试配置
    nginx -t
    
    # 重启Nginx
    systemctl restart nginx
    systemctl enable nginx
    
    log_success "Nginx配置完成"
}

# 配置防火墙
configure_firewall() {
    log_info "配置防火墙..."
    
    # 启用UFW
    ufw --force enable
    
    # 允许SSH
    ufw allow ssh
    
    # 允许HTTP和HTTPS
    ufw allow 80/tcp
    ufw allow 443/tcp
    
    # 显示状态
    ufw status
    
    log_success "防火墙配置完成"
}

# 创建管理脚本
create_management_scripts() {
    log_info "创建管理脚本..."
    
    APP_DIR="/opt/enterprise-system"
    
    # 启动脚本
    cat > $APP_DIR/start.sh << 'EOF'
#!/bin/bash
echo "启动企业管理系统..."
sudo systemctl start enterprise-system
sudo systemctl start nginx
echo "系统启动完成"
echo "访问地址: http://$(hostname -I | awk '{print $1}')"
EOF

    # 停止脚本
    cat > $APP_DIR/stop.sh << 'EOF'
#!/bin/bash
echo "停止企业管理系统..."
sudo systemctl stop enterprise-system
echo "系统停止完成"
EOF

    # 重启脚本
    cat > $APP_DIR/restart.sh << 'EOF'
#!/bin/bash
echo "重启企业管理系统..."
sudo systemctl restart enterprise-system
sudo systemctl restart nginx
echo "系统重启完成"
EOF

    # 状态检查脚本
    cat > $APP_DIR/status.sh << 'EOF'
#!/bin/bash
echo "=== 企业管理系统状态 ==="
echo "后端服务状态:"
sudo systemctl status enterprise-system --no-pager -l
echo ""
echo "Nginx状态:"
sudo systemctl status nginx --no-pager -l
echo ""
echo "端口监听状态:"
sudo netstat -tlnp | grep -E ':(80|8000)\s'
EOF

    # 日志查看脚本
    cat > $APP_DIR/logs.sh << 'EOF'
#!/bin/bash
echo "=== 企业管理系统日志 ==="
echo "后端服务日志:"
sudo journalctl -u enterprise-system -f --no-pager
EOF

    # 设置执行权限
    chmod +x $APP_DIR/*.sh
    chown enterprise:enterprise $APP_DIR/*.sh
    
    log_success "管理脚本创建完成"
}

# 启动服务
start_services() {
    log_info "启动服务..."
    
    # 启动后端服务
    systemctl start enterprise-system
    
    # 启动Nginx
    systemctl start nginx
    
    # 检查服务状态
    sleep 3
    
    if systemctl is-active --quiet enterprise-system; then
        log_success "后端服务启动成功"
    else
        log_error "后端服务启动失败"
        systemctl status enterprise-system
    fi
    
    if systemctl is-active --quiet nginx; then
        log_success "Nginx服务启动成功"
    else
        log_error "Nginx服务启动失败"
        systemctl status nginx
    fi
}

# 显示部署信息
show_deployment_info() {
    log_success "======================================"
    log_success "部署完成！"
    log_success "======================================"
    
    SERVER_IP=$(hostname -I | awk '{print $1}')
    
    echo -e "${GREEN}访问地址:${NC} http://$SERVER_IP"
    echo -e "${GREEN}应用目录:${NC} /opt/enterprise-system"
    echo -e "${GREEN}配置文件:${NC} /opt/enterprise-system/.env"
    echo -e "${GREEN}日志目录:${NC} /opt/enterprise-system/logs"
    echo ""
    echo -e "${YELLOW}重要提醒:${NC}"
    echo "1. 请编辑 /opt/enterprise-system/.env 文件，设置您的 DeepSeek API 密钥"
    echo "2. 重启服务使配置生效: sudo systemctl restart enterprise-system"
    echo "3. 查看服务状态: sudo systemctl status enterprise-system"
    echo "4. 查看日志: sudo journalctl -u enterprise-system -f"
    echo ""
    echo -e "${BLUE}管理命令:${NC}"
    echo "启动系统: /opt/enterprise-system/start.sh"
    echo "停止系统: /opt/enterprise-system/stop.sh"
    echo "重启系统: /opt/enterprise-system/restart.sh"
    echo "查看状态: /opt/enterprise-system/status.sh"
    echo "查看日志: /opt/enterprise-system/logs.sh"
    echo ""
    echo -e "${GREEN}部署文档:${NC} /opt/enterprise-system/DeepSeek_API_配置说明.md"
}

# 主函数
main() {
    log_info "开始部署小微企业大模型交互管理系统..."
    
    check_root
    update_system
    install_dependencies
    create_app_user
    create_directories
    copy_application
    create_venv
    install_python_deps
    setup_database
    create_config
    create_systemd_service
    configure_nginx
    configure_firewall
    create_management_scripts
    start_services
    show_deployment_info
    
    log_success "部署完成！"
}

# 执行主函数
main "$@"