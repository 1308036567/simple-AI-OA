# Git上传指南 - 小微企业大模型交互管理系统

## 📋 项目信息
- **GitHub仓库**: https://github.com/1308036567/Hardy.git
- **用户名**: 1308036567
- **邮箱**: mao1308036567@163.com
- **项目路径**: `c:\Users\13080\Desktop\小微企业大模型交互管理系统`

## 🚀 快速上传步骤

### 1. 打开命令提示符
按 `Win + R`，输入 `cmd`，按回车键打开命令提示符。

### 2. 进入项目目录
```cmd
cd "c:\Users\13080\Desktop\小微企业大模型交互管理系统"
```

### 3. 配置Git用户信息
```cmd
git config --global user.name "1308036567"
git config --global user.email "mao1308036567@163.com"
```

### 4. 初始化Git仓库
```cmd
git init
```

### 5. 添加远程仓库
```cmd
git remote add origin https://github.com/1308036567/Hardy.git
```

### 6. 添加所有文件
```cmd
git add .
```

### 7. 提交文件
```cmd
git commit -m "初始提交：小微企业大模型交互管理系统"
```

### 8. 推送到GitHub
```cmd
git push -u origin main
```

## 🔐 GitHub认证

当执行 `git push` 命令时，系统会提示输入用户名和密码：

- **用户名**: `1308036567`
- **密码**: 使用GitHub个人访问令牌（不是GitHub登录密码）

### 生成个人访问令牌

1. 登录GitHub账户
2. 点击右上角头像 → Settings
3. 左侧菜单选择 "Developer settings"
4. 选择 "Personal access tokens" → "Tokens (classic)"
5. 点击 "Generate new token" → "Generate new token (classic)"
6. 设置令牌信息：
   - **Note**: `Hardy项目上传`
   - **Expiration**: 选择过期时间（建议90天或更长）
   - **Select scopes**: 勾选 `repo`（完整仓库访问权限）
7. 点击 "Generate token"
8. **重要**: 复制生成的令牌并保存（只显示一次）

## 📁 项目结构

上传后的GitHub仓库结构：

```
Hardy/
├── .gitignore                  # Git忽略文件
├── README.md                   # 项目说明
├── Git上传指南.md              # 本指南文件
├── backend/                    # 后端代码
│   ├── main.py                # 应用入口
│   ├── config.py              # 配置文件
│   ├── database.py            # 数据库配置
│   ├── models.py              # 数据模型
│   ├── init_db.py             # 数据库初始化
│   ├── requirements.txt       # Python依赖
│   ├── routers/               # API路由
│   │   ├── accounts.py
│   │   ├── ai_chat.py
│   │   ├── employees.py
│   │   └── files.py
│   ├── schemas/               # 数据验证模式
│   │   ├── account.py
│   │   ├── ai_chat.py
│   │   ├── employee.py
│   │   └── file.py
│   └── utils/                 # 工具类
│       ├── ai_model.py
│       ├── backup.py
│       ├── chart_generator.py
│       ├── encryption.py
│       ├── excel_handler.py
│       ├── logger.py
│       └── validation.py
├── frontend/                   # 前端代码
│   ├── index.html             # 主页面
│   ├── css/
│   │   └── style.css          # 样式文件
│   └── js/
│       └── app.js             # 应用逻辑
├── docs/                       # 文档
│   ├── 技术文档.md
│   └── 模块解析.md
├── 小微企业管理系统项目立项书.md
└── 用于AI开发小微企业管理系统代码的提示词.md
```

## 🚫 被忽略的文件

以下文件和目录不会被上传到GitHub（已在.gitignore中配置）：

- `__pycache__/` - Python缓存文件
- `*.pyc`, `*.pyo` - Python编译文件
- `.env` - 环境配置文件（包含敏感信息）
- `logs/` - 日志文件
- `uploads/` - 用户上传文件
- `backups/` - 备份文件
- `models/` - AI模型文件（通常很大）
- `data/` - 数据文件
- `.vscode/`, `.idea/` - IDE配置文件

## 🔄 后续操作

### 更新代码
当您修改代码后，使用以下命令更新GitHub仓库：

```cmd
# 1. 添加修改的文件
git add .

# 2. 提交更改
git commit -m "描述您的更改内容"

# 3. 推送到GitHub
git push
```

### 克隆到其他设备
在其他电脑上获取项目代码：

```cmd
git clone https://github.com/1308036567/Hardy.git
cd Hardy
```

### 拉取最新代码
获取GitHub上的最新代码：

```cmd
git pull
```

## ⚠️ 注意事项

1. **个人访问令牌安全**：
   - 不要将令牌分享给他人
   - 定期更新令牌
   - 如果令牌泄露，立即删除并重新生成

2. **敏感信息保护**：
   - 确保`.env`文件不被上传
   - 数据库密码、API密钥等敏感信息不要提交到Git

3. **大文件处理**：
   - AI模型文件通常很大，不适合Git版本控制
   - 如需版本控制大文件，考虑使用Git LFS

4. **定期备份**：
   - 定期提交代码更改
   - 重要功能完成后及时推送到GitHub

## 🆘 常见问题解决

### 问题1：推送时提示认证失败
**解决方案**：
- 确认用户名正确：`1308036567`
- 确认使用个人访问令牌作为密码，而不是GitHub登录密码

### 问题2：文件太大无法推送
**解决方案**：
```cmd
# 查看大文件
git ls-files --others --ignored --exclude-standard

# 添加到.gitignore
echo "大文件路径" >> .gitignore
git add .gitignore
git commit -m "忽略大文件"
```

### 问题3：仓库已存在内容
**解决方案**：
```cmd
# 先拉取远程内容
git pull origin main --allow-unrelated-histories

# 解决冲突后再推送
git push
```

### 问题4：忘记个人访问令牌
**解决方案**：
- 重新生成新的个人访问令牌
- 删除旧令牌确保安全

## 📞 技术支持

如果遇到其他问题：
1. 检查网络连接
2. 确认GitHub服务状态
3. 查看Git错误信息
4. 参考GitHub官方文档

---

**祝您上传成功！** 🎉

项目上传后，您可以通过 https://github.com/1308036567/Hardy 访问您的代码仓库。