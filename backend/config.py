import os
from pydantic import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """系统配置类"""
    
    # 基础配置
    APP_NAME: str = "小微企业管理系统"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # 数据库配置
    DATABASE_URL: str = "mysql+pymysql://root:password@localhost:3306/enterprise_db"
    
    # 安全配置
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    AES_KEY: str = "your-aes-key-32-chars-long-here!"
    
    # 文件上传配置
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: list = [".jpg", ".jpeg", ".png", ".pdf", ".doc", ".docx", ".xls", ".xlsx"]
    
    # AI模型配置
    AI_MODEL_PATH: str = "models/chatglm-6b"
    VOSK_MODEL_PATH: str = "models/vosk-model-cn"
    
    # 备份配置
    BACKUP_DIR: str = "backups"
    BACKUP_RETENTION_DAYS: int = 30
    AUTO_BACKUP_TIME: str = "02:00"  # 每日凌晨2点自动备份
    
    # 日志配置
    LOG_DIR: str = "logs"
    LOG_LEVEL: str = "INFO"
    LOG_ROTATION: str = "1 day"
    LOG_RETENTION: str = "30 days"
    
    # FRP配置（内网穿透）
    FRP_SERVER_ADDR: str = "frp.example.com"
    FRP_SERVER_PORT: int = 7000
    FRP_TOKEN: str = "your-frp-token"
    FRP_LOCAL_PORT: int = 8000
    FRP_REMOTE_PORT: int = 8080
    
    # HTTPS配置
    SSL_CERT_PATH: Optional[str] = None
    SSL_KEY_PATH: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# 创建全局配置实例
settings = Settings()

# 数据库配置
DATABASE_CONFIG = {
    "url": settings.DATABASE_URL,
    "echo": settings.DEBUG,
    "pool_size": 10,
    "max_overflow": 20,
    "pool_pre_ping": True,
    "pool_recycle": 3600
}

# 员工信息字段映射配置
EMPLOYEE_FIELD_MAPPING = {
    "姓名": "name",
    "员工姓名": "name",
    "名字": "name",
    "身份证": "id_card",
    "身份证号": "id_card",
    "身份证号码": "id_card",
    "电话": "phone",
    "手机": "phone",
    "手机号": "phone",
    "联系电话": "phone",
    "银行卡": "bank_card",
    "银行卡号": "bank_card",
    "卡号": "bank_card",
    "开户行": "bank_name",
    "银行": "bank_name",
    "开户银行": "bank_name"
}

# 文件分类配置
FILE_CATEGORIES = {
    "员工档案": "employee_files",
    "项目支出凭证": "project_receipts",
    "财务报表": "financial_reports",
    "合同文件": "contracts",
    "其他文件": "others"
}

# AI指令模板
AI_COMMAND_TEMPLATES = {
    "添加员工": "添加员工{name}，身份证{id_card}，电话{phone}，银行卡{bank_card}，开户行{bank_name}",
    "生成工资表": "生成{project}工资表：{employees_salary}",
    "导出员工信息": "导出{condition}员工信息",
    "备份数据": "备份系统数据"
}