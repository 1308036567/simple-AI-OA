from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from config import DATABASE_CONFIG
import logging

logger = logging.getLogger(__name__)

# 创建数据库引擎
engine = create_engine(
    DATABASE_CONFIG["url"],
    echo=DATABASE_CONFIG["echo"],
    pool_size=DATABASE_CONFIG["pool_size"],
    max_overflow=DATABASE_CONFIG["max_overflow"],
    pool_pre_ping=DATABASE_CONFIG["pool_pre_ping"],
    pool_recycle=DATABASE_CONFIG["pool_recycle"]
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基础模型类
Base = declarative_base()

def get_db() -> Session:
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"数据库会话错误: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def init_database():
    """初始化数据库"""
    try:
        # 测试数据库连接
        with engine.connect() as conn:
            logger.info("数据库连接成功")
        
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        logger.info("数据库表创建完成")
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise

def get_db_session():
    """获取数据库会话（同步版本）"""
    return SessionLocal()