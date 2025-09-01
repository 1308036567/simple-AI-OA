# 小型公司信息管理系统

## 项目简介

这是一个基于Vue 3 + Flask的小型公司信息管理系统，集成了AI对话功能，用于管理员工信息、项目文件和财务数据。

## 技术栈

### 前端
- Vue 3
- Vite
- Element Plus
- Axios

### 后端
- Python Flask
- SQLite
- DeepSeek API

## 项目结构

```
OA/
├── frontend/          # Vue 3前端应用
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── vite.config.js
├── backend/           # Flask后端应用
│   ├── app.py
│   ├── models/
│   ├── routes/
│   ├── database/
│   └── requirements.txt
├── uploads/           # 文件上传目录
└── README.md
```

## 功能特性

1. **AI对话页面** - 支持自然语言查询和操作
2. **管理页面** - 数据仪表盘和功能导航
3. **员工管理** - 员工信息的增删改查
4. **文件管理** - 项目文件的上传下载
5. **财务管理** - 工资和开销记录管理

## 安装和运行

### 后端启动
```bash
cd backend
pip install -r requirements.txt
python app.py
```

### 前端启动
```bash
cd frontend
npm install
npm run dev
```

## 数据库设计

系统包含以下核心表：
- 项目表 (projects)
- 员工表 (employees)
- 文件表 (files)
- 工人工资表 (salaries)
- 项目开销表 (expenses)

## API接口

详细的API文档请参考后端代码中的路由定义。

## 部署说明

支持本地测试和轻量云服务器部署。