# 小微企业大模型交互管理系统

一个基于 B/S 架构的小微企业管理系统，专为手机端远程访问设计，集成本地大模型交互功能，实现员工信息管理、文件管理、账表管理等核心业务功能。

## 🚀 项目特色

- **手机端优先**: 专为移动设备优化的响应式界面
- **AI智能交互**: 集成本地大模型，支持语音指令和智能对话
- **远程访问**: 支持内网穿透，随时随地管理企业数据
- **数据安全**: 敏感信息加密存储，完整的操作日志
- **一键部署**: 简单的安装配置，快速上手

## 📋 功能模块

### 1. 员工信息管理
- ✅ 员工基础信息录入（姓名、身份证、电话、银行卡等）
- ✅ Excel批量导入，智能字段映射
- ✅ 员工信息查询、编辑、归档
- ✅ 员工数据导出
- ✅ AI指令批量操作

### 2. 文件管理系统
- ✅ 文件分类存储（员工档案、项目文档、财务凭证等）
- ✅ 文件上传、下载、预览
- ✅ 业务关联标记
- ✅ 文件搜索和筛选

### 3. 账表管理模块
- ✅ 工资表创建和管理
- ✅ 项目支出记录
- ✅ Excel导出功能
- ✅ 数据可视化图表
- ✅ AI指令生成账表

### 4. AI智能助手
- ✅ 文本对话交互
- ✅ 语音识别输入
- ✅ 指令解析执行
- ✅ 智能数据分析
- ✅ 对话历史管理

### 5. 数据安全与备份
- ✅ 敏感数据AES加密
- ✅ 完整操作日志
- ✅ 自动/手动备份
- ✅ 数据恢复功能

## 🛠 技术栈

### 后端
- **框架**: Python FastAPI
- **数据库**: SQLite/MySQL
- **ORM**: SQLAlchemy
- **加密**: Cryptography
- **文档处理**: openpyxl, python-docx
- **图表生成**: matplotlib, pyecharts
- **AI模型**: 本地大模型集成
- **语音处理**: SpeechRecognition, pyttsx3

### 前端
- **框架**: Vue 3
- **UI组件**: Vant (移动端)
- **HTTP客户端**: Axios
- **构建工具**: 原生HTML/CSS/JS

### 部署
- **服务器**: Uvicorn
- **内网穿透**: frp
- **容器化**: Docker (可选)

## 📦 安装部署

### 环境要求
- Python 3.8+
- Node.js 16+ (可选，用于前端开发)
- 现代浏览器支持

### 快速开始

1. **克隆项目**
```bash
git clone <repository-url>
cd 小微企业大模型交互管理系统
```

2. **安装后端依赖**
```bash
cd backend
pip install -r requirements.txt
```

3. **初始化数据库**
```bash
python init_db.py --action init
python init_db.py --action sample  # 可选：创建示例数据
```

4. **配置环境变量**
```bash
cp config/.env.example config/.env
# 编辑 .env 文件，配置数据库连接等参数
```

5. **启动后端服务**
```bash
python main.py
```

6. **访问前端**
- 本地访问: http://localhost:8000
- 手机访问: http://[服务器IP]:8000

### Docker 部署 (可选)

```bash
# 构建镜像
docker build -t sme-management .

# 运行容器
docker run -d -p 8000:8000 -v ./data:/app/data sme-management
```

## 🌐 远程访问配置

### 使用 frp 内网穿透

1. **下载 frp**
```bash
# 从 https://github.com/fatedier/frp/releases 下载对应版本
```

2. **配置 frp 客户端**
```ini
# frpc.ini
[common]
server_addr = your-frp-server.com
server_port = 7000
token = your-token

[sme-web]
type = http
local_ip = 127.0.0.1
local_port = 8000
custom_domains = your-domain.com
```

3. **启动 frp 客户端**
```bash
./frpc -c frpc.ini
```

### HTTPS 配置

使用 nginx 反向代理配置 SSL 证书：

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 📱 使用指南

### 基本操作

1. **员工管理**
   - 点击"员工管理"进入员工列表
   - 使用搜索框查找特定员工
   - 点击员工卡片查看详细信息
   - 长按员工卡片进行编辑或归档

2. **文件管理**
   - 选择文件分类进行筛选
   - 点击上传按钮添加新文件
   - 点击文件名进行预览或下载

3. **账表管理**
   - 创建新的工资表或支出表
   - 导出Excel格式的账表数据
   - 查看数据统计图表

### AI助手使用

1. **文本对话**
   - 在聊天界面输入问题或指令
   - AI会理解并执行相应操作
   - 支持复杂的业务查询和数据分析

2. **语音交互**
   - 点击麦克风按钮开始语音输入
   - 说出指令后松开按钮
   - AI会将语音转换为文字并执行

3. **常用指令示例**
   ```
   "添加员工张三，身份证110101199001011234"
   "查询技术部所有员工"
   "导出本月工资表"
   "创建项目A的支出记录"
   "备份系统数据"
   ```

## 🔧 配置说明

### 环境变量配置

```bash
# 数据库配置
DATABASE_URL=sqlite:///./data/sme.db
# DATABASE_URL=mysql://user:password@localhost/sme_db

# 加密密钥
ENCRYPTION_KEY=your-32-byte-encryption-key

# AI模型配置
AI_MODEL_PATH=./models/chatglm-6b
AI_MODEL_TYPE=chatglm

# 文件存储路径
FILE_STORAGE_PATH=./data/files

# 备份配置
BACKUP_PATH=./data/backups
BACKUP_RETENTION_DAYS=30

# 日志配置
LOG_LEVEL=INFO
LOG_FILE_PATH=./logs/app.log

# 服务器配置
HOST=0.0.0.0
PORT=8000
DEBUG=False
```

### AI模型配置

1. **下载模型文件**
   - ChatGLM-6B: https://huggingface.co/THUDM/chatglm-6b
   - 其他兼容模型

2. **配置模型路径**
   ```python
   # config/settings.py
   AI_MODEL_CONFIG = {
       "model_path": "./models/chatglm-6b",
       "model_type": "chatglm",
       "device": "auto",  # auto, cpu, cuda
       "precision": "fp16"
   }
   ```

## 📊 API 文档

启动服务后访问 http://localhost:8000/docs 查看完整的 API 文档。

### 主要 API 端点

#### 员工管理
- `GET /api/employees/` - 获取员工列表
- `POST /api/employees/` - 创建员工
- `PUT /api/employees/{id}` - 更新员工信息
- `DELETE /api/employees/{id}` - 删除员工
- `POST /api/employees/import` - 批量导入员工
- `GET /api/employees/export` - 导出员工数据

#### 文件管理
- `GET /api/files/` - 获取文件列表
- `POST /api/files/upload` - 上传文件
- `GET /api/files/{id}/download` - 下载文件
- `DELETE /api/files/{id}` - 删除文件

#### 账表管理
- `GET /api/accounts/` - 获取账表列表
- `POST /api/accounts/` - 创建账表
- `POST /api/accounts/{id}/salary` - 添加工资记录
- `POST /api/accounts/{id}/expense` - 添加支出记录
- `GET /api/accounts/{id}/export` - 导出账表
- `GET /api/accounts/{id}/chart` - 生成图表

#### AI交互
- `POST /api/ai/chat` - 文本对话
- `POST /api/ai/voice` - 语音对话
- `GET /api/ai/history` - 获取对话历史
- `POST /api/ai/execute` - 执行AI指令

## 🔒 安全特性

### 数据加密
- 身份证号码使用AES-256加密存储
- 银行卡号使用AES-256加密存储
- 手机号码使用AES-256加密存储
- 密码使用bcrypt哈希存储

### 访问控制
- API请求频率限制
- 文件上传类型和大小限制
- SQL注入防护
- XSS攻击防护

### 操作审计
- 完整的操作日志记录
- 用户行为追踪
- 数据变更历史
- 异常操作告警

## 🧪 测试

### 运行测试
```bash
# 安装测试依赖
pip install pytest pytest-asyncio httpx

# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_employees.py

# 生成覆盖率报告
pytest --cov=. --cov-report=html
```

### 测试用例
- 员工管理功能测试
- 文件上传下载测试
- 账表创建导出测试
- AI对话功能测试
- 数据加密解密测试
- API接口测试

## 📈 性能优化

### 数据库优化
- 合理的索引设计
- 查询语句优化
- 连接池配置
- 分页查询实现

### 文件处理优化
- 大文件分块上传
- 文件压缩存储
- 缓存机制
- CDN加速（可选）

### AI模型优化
- 模型量化加速
- 批处理优化
- 缓存常用响应
- 异步处理

## 🚨 故障排除

### 常见问题

1. **数据库连接失败**
   ```bash
   # 检查数据库配置
   python -c "from config.database import get_database_url; print(get_database_url())"
   
   # 重新初始化数据库
   python init_db.py --action init
   ```

2. **AI模型加载失败**
   ```bash
   # 检查模型路径
   ls -la ./models/
   
   # 检查模型配置
   python -c "from utils.ai_model import AIModelManager; print(AIModelManager().get_model_status())"
   ```

3. **文件上传失败**
   ```bash
   # 检查存储目录权限
   ls -la ./data/files/
   
   # 创建存储目录
   mkdir -p ./data/files
   chmod 755 ./data/files
   ```

4. **远程访问问题**
   - 检查防火墙设置
   - 确认端口开放状态
   - 验证frp配置
   - 检查域名解析

### 日志查看
```bash
# 查看应用日志
tail -f ./logs/app.log

# 查看错误日志
tail -f ./logs/error.log

# 查看访问日志
tail -f ./logs/access.log
```

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

### 开发规范
- 遵循PEP 8代码规范
- 编写单元测试
- 更新相关文档
- 提交前运行测试
