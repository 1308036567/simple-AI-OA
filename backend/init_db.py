#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库初始化脚本
用于创建数据库表结构和初始化数据
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from database import Base, get_database_url
from models import (
    Employee, FileRecord, AccountTable, SalaryRecord, 
    ExpenseRecord, AIChat, OperationLog, BackupRecord
)
from config import DATABASE_CONFIG
from utils.logger import get_logger
from utils.encryption import get_encryption_manager
import logging

logger = get_logger('init_db')

def create_database_if_not_exists():
    """创建数据库（如果不存在）"""
    try:
        if DATABASE_CONFIG['type'] == 'mysql':
            # MySQL数据库创建
            admin_url = (
                f"mysql+pymysql://{DATABASE_CONFIG['user']}:{DATABASE_CONFIG['password']}"
                f"@{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}"
            )
            
            admin_engine = create_engine(admin_url)
            
            with admin_engine.connect() as conn:
                # 检查数据库是否存在
                result = conn.execute(
                    text(f"SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '{DATABASE_CONFIG['database']}'")
                )
                
                if not result.fetchone():
                    # 创建数据库
                    conn.execute(text(f"CREATE DATABASE {DATABASE_CONFIG['database']} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
                    conn.commit()
                    logger.info(f"数据库 {DATABASE_CONFIG['database']} 创建成功")
                else:
                    logger.info(f"数据库 {DATABASE_CONFIG['database']} 已存在")
            
            admin_engine.dispose()
            
        elif DATABASE_CONFIG['type'] == 'sqlite':
            # SQLite数据库文件会自动创建
            db_path = Path(DATABASE_CONFIG['database'])
            db_path.parent.mkdir(parents=True, exist_ok=True)
            logger.info(f"SQLite数据库路径: {db_path}")
            
    except Exception as e:
        logger.error(f"创建数据库失败: {e}")
        raise

def create_tables():
    """创建数据库表"""
    try:
        database_url = get_database_url()
        engine = create_engine(database_url, echo=True)
        
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        logger.info("数据库表创建成功")
        
        engine.dispose()
        
    except Exception as e:
        logger.error(f"创建数据库表失败: {e}")
        raise

def insert_initial_data():
    """插入初始数据"""
    try:
        from database import SessionLocal
        
        db = SessionLocal()
        
        try:
            # 检查是否已有数据
            existing_employees = db.query(Employee).count()
            if existing_employees > 0:
                logger.info("数据库已有数据，跳过初始数据插入")
                return
            
            encryption_manager = get_encryption_manager()
            
            # 插入示例员工数据
            sample_employees = [
                {
                    'name': '张三',
                    'id_card': '110101199001011234',
                    'phone': '13800138001',
                    'bank_card': '6222021234567890123',
                    'bank_name': '中国工商银行',
                    'department': '技术部',
                    'position': '软件工程师',
                    'hire_date': '2024-01-15',
                    'is_archived': False
                },
                {
                    'name': '李四',
                    'id_card': '110101199002021234',
                    'phone': '13800138002',
                    'bank_card': '6222021234567890124',
                    'bank_name': '中国建设银行',
                    'department': '财务部',
                    'position': '会计师',
                    'hire_date': '2024-02-01',
                    'is_archived': False
                },
                {
                    'name': '王五',
                    'id_card': '110101199003031234',
                    'phone': '13800138003',
                    'bank_card': '6222021234567890125',
                    'bank_name': '中国农业银行',
                    'department': '销售部',
                    'position': '销售经理',
                    'hire_date': '2024-01-20',
                    'is_archived': False
                }
            ]
            
            for emp_data in sample_employees:
                employee = Employee(
                    name=emp_data['name'],
                    id_card=encryption_manager.encrypt_data(emp_data['id_card']),
                    phone=encryption_manager.encrypt_data(emp_data['phone']),
                    bank_card=encryption_manager.encrypt_data(emp_data['bank_card']),
                    bank_name=emp_data['bank_name'],
                    department=emp_data['department'],
                    position=emp_data['position'],
                    hire_date=emp_data['hire_date'],
                    is_archived=emp_data['is_archived']
                )
                db.add(employee)
            
            # 插入示例账表
            account_table = AccountTable(
                table_name='2024年1月工资表',
                table_type='salary',
                description='2024年1月份员工工资发放表',
                created_by='admin'
            )
            db.add(account_table)
            db.flush()  # 获取account_table的ID
            
            # 插入示例工资记录
            employees = db.query(Employee).all()
            base_salaries = [8000, 6000, 10000]  # 对应张三、李四、王五的基本工资
            
            for i, employee in enumerate(employees[:3]):
                salary_record = SalaryRecord(
                    account_table_id=account_table.id,
                    employee_id=employee.id,
                    employee_name=employee.name,
                    salary_amount=base_salaries[i],
                    bonus=500 if i == 2 else 0,  # 王五有奖金
                    deduction=100 if i == 1 else 0,  # 李四有扣款
                    pay_date='2024-01-31',
                    remark='首月工资' if i == 0 else ''
                )
                db.add(salary_record)
            
            # 插入示例支出记录
            expense_records = [
                {
                    'account_table_id': account_table.id,
                    'expense_type': '办公用品',
                    'description': '购买打印纸、文具等办公用品',
                    'amount': 500.00,
                    'expense_date': '2024-01-15',
                    'recipient': '办公用品商店',
                    'remark': '月度采购'
                },
                {
                    'account_table_id': account_table.id,
                    'expense_type': '差旅费',
                    'description': '员工出差交通住宿费用',
                    'amount': 1200.00,
                    'expense_date': '2024-01-20',
                    'recipient': '张三',
                    'remark': '客户拜访出差'
                }
            ]
            
            for exp_data in expense_records:
                expense_record = ExpenseRecord(**exp_data)
                db.add(expense_record)
            
            # 提交事务
            db.commit()
            logger.info("初始数据插入成功")
            
        except Exception as e:
            db.rollback()
            logger.error(f"插入初始数据失败: {e}")
            raise
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"初始化数据失败: {e}")
        raise

def create_indexes():
    """创建数据库索引"""
    try:
        from database import SessionLocal
        
        db = SessionLocal()
        
        try:
            # 创建常用查询的索引
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_employee_name ON employees(name)",
                "CREATE INDEX IF NOT EXISTS idx_employee_department ON employees(department)",
                "CREATE INDEX IF NOT EXISTS idx_employee_archived ON employees(is_archived)",
                "CREATE INDEX IF NOT EXISTS idx_file_category ON file_records(category)",
                "CREATE INDEX IF NOT EXISTS idx_file_business_id ON file_records(business_id)",
                "CREATE INDEX IF NOT EXISTS idx_salary_employee ON salary_records(employee_id)",
                "CREATE INDEX IF NOT EXISTS idx_salary_date ON salary_records(pay_date)",
                "CREATE INDEX IF NOT EXISTS idx_expense_type ON expense_records(expense_type)",
                "CREATE INDEX IF NOT EXISTS idx_expense_date ON expense_records(expense_date)",
                "CREATE INDEX IF NOT EXISTS idx_operation_type ON operation_logs(operation_type)",
                "CREATE INDEX IF NOT EXISTS idx_operation_date ON operation_logs(created_at)",
                "CREATE INDEX IF NOT EXISTS idx_ai_chat_session ON ai_chats(session_id)",
                "CREATE INDEX IF NOT EXISTS idx_backup_date ON backup_records(created_at)"
            ]
            
            for index_sql in indexes:
                try:
                    db.execute(text(index_sql))
                    db.commit()
                except Exception as e:
                    logger.warning(f"创建索引失败: {index_sql}, 错误: {e}")
                    db.rollback()
            
            logger.info("数据库索引创建完成")
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"创建数据库索引失败: {e}")
        # 索引创建失败不应该阻止系统启动
        pass

def check_database_connection():
    """检查数据库连接"""
    try:
        from database import SessionLocal
        
        db = SessionLocal()
        try:
            # 执行简单查询测试连接
            result = db.execute(text("SELECT 1"))
            result.fetchone()
            logger.info("数据库连接测试成功")
            return True
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"数据库连接测试失败: {e}")
        return False

def main():
    """主函数"""
    try:
        logger.info("开始初始化数据库...")
        
        # 1. 创建数据库（如果不存在）
        logger.info("步骤 1: 创建数据库")
        create_database_if_not_exists()
        
        # 2. 创建表结构
        logger.info("步骤 2: 创建数据库表")
        create_tables()
        
        # 3. 检查数据库连接
        logger.info("步骤 3: 检查数据库连接")
        if not check_database_connection():
            raise Exception("数据库连接失败")
        
        # 4. 创建索引
        logger.info("步骤 4: 创建数据库索引")
        create_indexes()
        
        # 5. 插入初始数据
        logger.info("步骤 5: 插入初始数据")
        insert_initial_data()
        
        logger.info("数据库初始化完成！")
        
        # 显示初始化结果
        print("\n" + "="*50)
        print("数据库初始化成功！")
        print("="*50)
        print(f"数据库类型: {DATABASE_CONFIG['type']}")
        if DATABASE_CONFIG['type'] == 'mysql':
            print(f"数据库地址: {DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}")
            print(f"数据库名称: {DATABASE_CONFIG['database']}")
        else:
            print(f"数据库文件: {DATABASE_CONFIG['database']}")
        print("\n已创建的表:")
        print("- employees (员工信息表)")
        print("- file_records (文件记录表)")
        print("- account_tables (账表信息表)")
        print("- salary_records (工资记录表)")
        print("- expense_records (支出记录表)")
        print("- ai_chats (AI对话记录表)")
        print("- operation_logs (操作日志表)")
        print("- backup_records (备份记录表)")
        print("\n已插入示例数据:")
        print("- 3个示例员工")
        print("- 1个示例账表")
        print("- 3条工资记录")
        print("- 2条支出记录")
        print("\n现在可以启动应用程序了！")
        print("="*50)
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        print(f"\n数据库初始化失败: {e}")
        print("请检查数据库配置和连接设置")
        sys.exit(1)

if __name__ == "__main__":
    # 设置日志级别
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    main()