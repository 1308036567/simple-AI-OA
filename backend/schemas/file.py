from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime

class FileRecordBase(BaseModel):
    """文件记录基础模型"""
    category: str
    business_id: Optional[str] = None
    description: Optional[str] = None
    
    @validator('category')
    def validate_category(cls, v):
        valid_categories = ["员工档案", "项目支出凭证", "财务报表", "合同文件", "其他文件"]
        if v not in valid_categories:
            raise ValueError(f'无效的文件分类，支持的分类：{", ".join(valid_categories)}')
        return v

class FileUploadRequest(FileRecordBase):
    """文件上传请求模型"""
    pass

class FileRecordResponse(BaseModel):
    """文件记录响应模型"""
    id: int
    filename: str
    original_filename: str
    file_size: int
    file_type: str
    category: str
    business_id: Optional[str]
    description: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class FileUploadResponse(BaseModel):
    """文件上传响应模型"""
    id: int
    filename: str
    original_filename: str
    file_size: int
    category: str
    message: str

class FileUpdateRequest(BaseModel):
    """文件信息更新请求模型"""
    category: Optional[str] = None
    business_id: Optional[str] = None
    description: Optional[str] = None
    
    @validator('category')
    def validate_category(cls, v):
        if v is not None:
            valid_categories = ["员工档案", "项目支出凭证", "财务报表", "合同文件", "其他文件"]
            if v not in valid_categories:
                raise ValueError(f'无效的文件分类，支持的分类：{", ".join(valid_categories)}')
        return v

class FileSearchRequest(BaseModel):
    """文件搜索请求模型"""
    category: Optional[str] = None
    business_id: Optional[str] = None
    keyword: Optional[str] = None
    skip: int = 0
    limit: int = 100

class FileListResponse(BaseModel):
    """文件列表响应模型"""
    files: list[FileRecordResponse]
    total: int
    skip: int
    limit: int

class FileCategoryResponse(BaseModel):
    """文件分类响应模型"""
    categories: list[str]
    mapping: dict[str, str]