from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, LargeBinary
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from datetime import datetime

class Employee(Base):
    """员工信息模型"""
    __tablename__ = "employees"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="姓名")
    id_card = Column(LargeBinary, nullable=False, comment="身份证号（加密存储）")
    phone = Column(String(20), nullable=False, comment="电话号码")
    bank_card = Column(LargeBinary, nullable=True, comment="银行卡号（加密存储）")
    bank_name = Column(String(100), nullable=True, comment="开户行")
    is_archived = Column(Boolean, default=False, comment="是否归档")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关联关系
    salary_records = relationship("SalaryRecord", back_populates="employee")
    
class FileRecord(Base):
    """文件记录模型"""
    __tablename__ = "file_records"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False, comment="文件名")
    original_filename = Column(String(255), nullable=False, comment="原始文件名")
    file_path = Column(String(500), nullable=False, comment="文件路径")
    file_size = Column(Integer, nullable=False, comment="文件大小（字节）")
    file_type = Column(String(50), nullable=False, comment="文件类型")
    category = Column(String(50), nullable=False, comment="文件分类")
    business_id = Column(String(100), nullable=True, comment="关联业务ID")
    description = Column(Text, nullable=True, comment="文件描述")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    
class AccountTable(Base):
    """账表模型"""
    __tablename__ = "account_tables"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, comment="账表名称")
    table_type = Column(String(50), nullable=False, comment="账表类型")
    description = Column(Text, nullable=True, comment="账表描述")
    file_path = Column(String(500), nullable=True, comment="生成的文件路径")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关联关系
    salary_records = relationship("SalaryRecord", back_populates="account_table")
    expense_records = relationship("ExpenseRecord", back_populates="account_table")

class SalaryRecord(Base):
    """工资记录模型"""
    __tablename__ = "salary_records"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    account_table_id = Column(Integer, ForeignKey("account_tables.id"), nullable=False)
    project_name = Column(String(200), nullable=True, comment="项目名称")
    salary_amount = Column(Float, nullable=False, comment="工资金额")
    bonus = Column(Float, default=0, comment="奖金")
    deduction = Column(Float, default=0, comment="扣款")
    actual_amount = Column(Float, nullable=False, comment="实际金额")
    pay_date = Column(DateTime, nullable=True, comment="发放日期")
    remark = Column(Text, nullable=True, comment="备注")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    
    # 关联关系
    employee = relationship("Employee", back_populates="salary_records")
    account_table = relationship("AccountTable", back_populates="salary_records")

class ExpenseRecord(Base):
    """支出记录模型"""
    __tablename__ = "expense_records"
    
    id = Column(Integer, primary_key=True, index=True)
    account_table_id = Column(Integer, ForeignKey("account_tables.id"), nullable=False)
    project_name = Column(String(200), nullable=False, comment="项目名称")
    expense_type = Column(String(100), nullable=False, comment="支出类型")
    amount = Column(Float, nullable=False, comment="支出金额")
    expense_date = Column(DateTime, nullable=False, comment="支出日期")
    description = Column(Text, nullable=True, comment="支出描述")
    receipt_file_id = Column(Integer, ForeignKey("file_records.id"), nullable=True, comment="凭证文件ID")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    
    # 关联关系
    account_table = relationship("AccountTable", back_populates="expense_records")
    receipt_file = relationship("FileRecord")

class AIChat(Base):
    """AI对话记录模型"""
    __tablename__ = "ai_chats"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), nullable=False, comment="会话ID")
    user_input = Column(Text, nullable=False, comment="用户输入")
    user_input_type = Column(String(20), default="text", comment="输入类型：text/voice")
    ai_response = Column(Text, nullable=False, comment="AI响应")
    command_type = Column(String(50), nullable=True, comment="指令类型")
    execution_result = Column(Text, nullable=True, comment="执行结果")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")

class OperationLog(Base):
    """操作日志模型"""
    __tablename__ = "operation_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    operation_type = Column(String(50), nullable=False, comment="操作类型")
    operation_detail = Column(Text, nullable=False, comment="操作详情")
    operator = Column(String(100), default="system", comment="操作人")
    ip_address = Column(String(50), nullable=True, comment="IP地址")
    user_agent = Column(String(500), nullable=True, comment="用户代理")
    created_at = Column(DateTime, default=func.now(), comment="操作时间")

class BackupRecord(Base):
    """备份记录模型"""
    __tablename__ = "backup_records"
    
    id = Column(Integer, primary_key=True, index=True)
    backup_type = Column(String(20), nullable=False, comment="备份类型：auto/manual")
    backup_path = Column(String(500), nullable=False, comment="备份文件路径")
    backup_size = Column(Integer, nullable=False, comment="备份文件大小")
    status = Column(String(20), default="success", comment="备份状态")
    error_message = Column(Text, nullable=True, comment="错误信息")
    created_at = Column(DateTime, default=func.now(), comment="备份时间")