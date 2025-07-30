from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import uvicorn
import os
from datetime import datetime
import logging

from database import get_db, engine
from models import Base
from routers import employees, files, accounts, ai_chat
from utils.logger import setup_logger
from utils.backup import BackupManager
from config import settings

# 创建数据库表
Base.metadata.create_all(bind=engine)

# 初始化FastAPI应用
app = FastAPI(
    title="小微企业管理系统",
    description="基于FastAPI的小微企业管理系统，支持员工管理、文件管理、账表管理和AI交互",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# 设置日志
setup_logger()
logger = logging.getLogger(__name__)

# 注册路由
app.include_router(employees.router, prefix="/api/employees", tags=["员工管理"])
app.include_router(files.router, prefix="/api/files", tags=["文件管理"])
app.include_router(accounts.router, prefix="/api/accounts", tags=["账表管理"])
app.include_router(ai_chat.router, prefix="/api/ai", tags=["AI交互"])

# 初始化备份管理器
backup_manager = BackupManager()

@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("小微企业管理系统启动")
    
    # 创建必要的目录
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("static", exist_ok=True)
    os.makedirs("backups", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    # 启动定时备份
    backup_manager.start_scheduled_backup()
    
    logger.info("系统初始化完成")

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("小微企业管理系统关闭")
    backup_manager.stop_scheduled_backup()

@app.get("/")
async def root():
    """根路径，返回系统信息"""
    return {
        "message": "小微企业管理系统API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )