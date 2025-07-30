from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

class AccountTableBase(BaseModel):
    """账表基础模型"""
    name: str
    table_type: str
    description: Optional[str] = None
    
    @validator('name')
    def validate_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('账表名称不能为空')
        if len(v) > 200:
            raise ValueError('账表名称长度不能超过200个字符')
        return v.strip()
    
    @validator('table_type')
    def validate_table_type(cls, v):
        valid_types = ['salary', 'expense', 'income', 'other']
        if v not in valid_types:
            raise ValueError(f'无效的账表类型，支持的类型：{", ".join(valid_types)}')
        return v

class AccountTableCreate(AccountTableBase):
    """创建账表请求模型"""
    pass

class AccountTableUpdate(BaseModel):
    """更新账表请求模型"""
    name: Optional[str] = None
    description: Optional[str] = None
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None:
            if not v or len(v.strip()) == 0:
                raise ValueError('账表名称不能为空')
            if len(v) > 200:
                raise ValueError('账表名称长度不能超过200个字符')
        return v.strip() if v else v

class AccountTableResponse(AccountTableBase):
    """账表响应模型"""
    id: int
    file_path: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class SalaryRecordBase(BaseModel):
    """工资记录基础模型"""
    employee_id: int
    project_name: Optional[str] = None
    salary_amount: float
    bonus: float = 0
    deduction: float = 0
    pay_date: Optional[datetime] = None
    remark: Optional[str] = None
    
    @validator('salary_amount', 'bonus', 'deduction')
    def validate_amounts(cls, v):
        if v < 0:
            raise ValueError('金额不能为负数')
        return round(v, 2)

class SalaryRecordCreate(SalaryRecordBase):
    """创建工资记录请求模型"""
    pass

class SalaryRecordUpdate(BaseModel):
    """更新工资记录请求模型"""
    project_name: Optional[str] = None
    salary_amount: Optional[float] = None
    bonus: Optional[float] = None
    deduction: Optional[float] = None
    pay_date: Optional[datetime] = None
    remark: Optional[str] = None
    
    @validator('salary_amount', 'bonus', 'deduction')
    def validate_amounts(cls, v):
        if v is not None and v < 0:
            raise ValueError('金额不能为负数')
        return round(v, 2) if v is not None else v

class SalaryRecordResponse(SalaryRecordBase):
    """工资记录响应模型"""
    id: int
    employee_name: str
    account_table_id: int
    actual_amount: float
    created_at: datetime
    
    class Config:
        from_attributes = True

class ExpenseRecordBase(BaseModel):
    """支出记录基础模型"""
    project_name: str
    expense_type: str
    amount: float
    expense_date: datetime
    description: Optional[str] = None
    receipt_file_id: Optional[int] = None
    
    @validator('project_name')
    def validate_project_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('项目名称不能为空')
        return v.strip()
    
    @validator('expense_type')
    def validate_expense_type(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('支出类型不能为空')
        return v.strip()
    
    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('支出金额必须大于0')
        return round(v, 2)

class ExpenseRecordCreate(ExpenseRecordBase):
    """创建支出记录请求模型"""
    pass

class ExpenseRecordUpdate(BaseModel):
    """更新支出记录请求模型"""
    project_name: Optional[str] = None
    expense_type: Optional[str] = None
    amount: Optional[float] = None
    expense_date: Optional[datetime] = None
    description: Optional[str] = None
    receipt_file_id: Optional[int] = None
    
    @validator('amount')
    def validate_amount(cls, v):
        if v is not None and v <= 0:
            raise ValueError('支出金额必须大于0')
        return round(v, 2) if v is not None else v

class ExpenseRecordResponse(ExpenseRecordBase):
    """支出记录响应模型"""
    id: int
    account_table_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class BatchSalaryCreate(BaseModel):
    """批量创建工资记录请求模型"""
    table_id: int
    project_name: Optional[str] = None
    salary_data: List[dict]
    
    @validator('salary_data')
    def validate_salary_data(cls, v):
        if not v:
            raise ValueError('工资数据不能为空')
        
        required_fields = ['name', 'amount']
        for item in v:
            for field in required_fields:
                if field not in item:
                    raise ValueError(f'工资数据缺少必要字段：{field}')
            
            if not isinstance(item['amount'], (int, float)) or item['amount'] <= 0:
                raise ValueError('工资金额必须为正数')
        
        return v

class AccountStatistics(BaseModel):
    """账表统计信息模型"""
    type: str
    total_records: int
    total_amount: float
    average_amount: float
    details: dict

class ChartRequest(BaseModel):
    """图表生成请求模型"""
    table_id: int
    chart_type: str = 'bar'
    
    @validator('chart_type')
    def validate_chart_type(cls, v):
        valid_types = ['bar', 'pie', 'line', 'scatter']
        if v not in valid_types:
            raise ValueError(f'无效的图表类型，支持的类型：{", ".join(valid_types)}')
        return v

class ExportRequest(BaseModel):
    """导出请求模型"""
    table_id: int
    format: str = 'excel'
    include_charts: bool = False
    
    @validator('format')
    def validate_format(cls, v):
        valid_formats = ['excel', 'pdf', 'csv']
        if v not in valid_formats:
            raise ValueError(f'无效的导出格式，支持的格式：{", ".join(valid_formats)}')
        return v