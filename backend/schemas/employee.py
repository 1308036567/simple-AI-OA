from pydantic import BaseModel, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import re

class EmployeeBase(BaseModel):
    """员工基础模型"""
    name: str
    phone: str
    bank_card: Optional[str] = None
    bank_name: Optional[str] = None
    
    @validator('name')
    def validate_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('姓名不能为空')
        if len(v) > 50:
            raise ValueError('姓名长度不能超过50个字符')
        return v.strip()
    
    @validator('phone')
    def validate_phone(cls, v):
        if not re.match(r'^1[3-9]\d{9}$', v):
            raise ValueError('手机号格式不正确')
        return v

class EmployeeCreate(EmployeeBase):
    """创建员工请求模型"""
    id_card: str
    
    @validator('id_card')
    def validate_id_card(cls, v):
        # 简化的身份证号验证
        if not re.match(r'^\d{17}[\dXx]$', v):
            raise ValueError('身份证号格式不正确')
        return v.upper()

class EmployeeUpdate(EmployeeBase):
    """更新员工请求模型"""
    name: Optional[str] = None
    id_card: Optional[str] = None
    phone: Optional[str] = None
    is_archived: Optional[bool] = None
    
    @validator('id_card')
    def validate_id_card(cls, v):
        if v and not re.match(r'^\d{17}[\dXx]$', v):
            raise ValueError('身份证号格式不正确')
        return v.upper() if v else v

class EmployeeResponse(EmployeeBase):
    """员工响应模型"""
    id: int
    id_card: str
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class EmployeeImportPreview(BaseModel):
    """员工导入预览模型"""
    total_rows: int
    valid_rows: int
    invalid_rows: int
    field_mapping: Dict[str, str]
    sample_data: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]

class EmployeeImportResult(BaseModel):
    """员工导入结果模型"""
    success_count: int
    error_count: int
    errors: List[Dict[str, str]]
    message: str

class EmployeeSearchRequest(BaseModel):
    """员工搜索请求模型"""
    keyword: Optional[str] = None
    include_archived: bool = False
    skip: int = 0
    limit: int = 100

class EmployeeListResponse(BaseModel):
    """员工列表响应模型"""
    employees: List[EmployeeResponse]
    total: int
    skip: int
    limit: int