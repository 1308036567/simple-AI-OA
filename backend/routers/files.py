from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid
from datetime import datetime
import shutil

from database import get_db
from models import FileRecord, OperationLog
from schemas.file import FileRecordResponse, FileUploadResponse
from utils.logger import log_operation
from config import settings, FILE_CATEGORIES

router = APIRouter()

@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    category: str = Form(...),
    business_id: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """上传文件"""
    try:
        # 验证文件类型
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400, 
                detail=f"不支持的文件类型：{file_ext}"
            )
        
        # 验证文件大小
        file_content = await file.read()
        if len(file_content) > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"文件大小超过限制：{settings.MAX_FILE_SIZE / 1024 / 1024}MB"
            )
        
        # 验证分类
        if category not in FILE_CATEGORIES:
            raise HTTPException(status_code=400, detail="无效的文件分类")
        
        # 生成唯一文件名
        file_id = str(uuid.uuid4())
        filename = f"{file_id}{file_ext}"
        
        # 创建分类目录
        category_dir = os.path.join(settings.UPLOAD_DIR, FILE_CATEGORIES[category])
        os.makedirs(category_dir, exist_ok=True)
        
        # 保存文件
        file_path = os.path.join(category_dir, filename)
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)
        
        # 创建文件记录
        db_file = FileRecord(
            filename=filename,
            original_filename=file.filename,
            file_path=file_path,
            file_size=len(file_content),
            file_type=file_ext,
            category=category,
            business_id=business_id,
            description=description
        )
        
        db.add(db_file)
        db.commit()
        db.refresh(db_file)
        
        # 记录操作日志
        await log_operation(
            db=db,
            operation_type="UPLOAD_FILE",
            operation_detail=f"上传文件：{file.filename}，分类：{category}"
        )
        
        return FileUploadResponse(
            id=db_file.id,
            filename=db_file.filename,
            original_filename=db_file.original_filename,
            file_size=db_file.file_size,
            category=db_file.category,
            message="文件上传成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # 清理已上传的文件
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        
        db.rollback()
        raise HTTPException(status_code=500, detail=f"文件上传失败：{str(e)}")

@router.get("/", response_model=List[FileRecordResponse])
async def get_files(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    business_id: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取文件列表"""
    try:
        query = db.query(FileRecord)
        
        # 按分类筛选
        if category:
            query = query.filter(FileRecord.category == category)
        
        # 按业务ID筛选
        if business_id:
            query = query.filter(FileRecord.business_id == business_id)
        
        # 搜索功能
        if search:
            query = query.filter(
                FileRecord.original_filename.contains(search) |
                FileRecord.description.contains(search)
            )
        
        files = query.order_by(FileRecord.created_at.desc()).offset(skip).limit(limit).all()
        
        return [
            FileRecordResponse(
                id=file.id,
                filename=file.filename,
                original_filename=file.original_filename,
                file_size=file.file_size,
                file_type=file.file_type,
                category=file.category,
                business_id=file.business_id,
                description=file.description,
                created_at=file.created_at
            )
            for file in files
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文件列表失败：{str(e)}")

@router.get("/categories")
async def get_file_categories():
    """获取文件分类列表"""
    return {
        "categories": list(FILE_CATEGORIES.keys()),
        "mapping": FILE_CATEGORIES
    }

@router.get("/{file_id}", response_model=FileRecordResponse)
async def get_file_info(file_id: int, db: Session = Depends(get_db)):
    """获取文件信息"""
    try:
        file_record = db.query(FileRecord).filter(FileRecord.id == file_id).first()
        
        if not file_record:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        return FileRecordResponse(
            id=file_record.id,
            filename=file_record.filename,
            original_filename=file_record.original_filename,
            file_size=file_record.file_size,
            file_type=file_record.file_type,
            category=file_record.category,
            business_id=file_record.business_id,
            description=file_record.description,
            created_at=file_record.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文件信息失败：{str(e)}")

@router.get("/{file_id}/download")
async def download_file(file_id: int, db: Session = Depends(get_db)):
    """下载文件"""
    try:
        file_record = db.query(FileRecord).filter(FileRecord.id == file_id).first()
        
        if not file_record:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        if not os.path.exists(file_record.file_path):
            raise HTTPException(status_code=404, detail="文件已被删除")
        
        # 记录操作日志
        await log_operation(
            db=db,
            operation_type="DOWNLOAD_FILE",
            operation_detail=f"下载文件：{file_record.original_filename}"
        )
        
        return FileResponse(
            path=file_record.file_path,
            filename=file_record.original_filename,
            media_type="application/octet-stream"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"下载文件失败：{str(e)}")

@router.put("/{file_id}")
async def update_file_info(
    file_id: int,
    category: Optional[str] = Form(None),
    business_id: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """更新文件信息"""
    try:
        file_record = db.query(FileRecord).filter(FileRecord.id == file_id).first()
        
        if not file_record:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 更新字段
        if category is not None:
            if category not in FILE_CATEGORIES:
                raise HTTPException(status_code=400, detail="无效的文件分类")
            file_record.category = category
        
        if business_id is not None:
            file_record.business_id = business_id
        
        if description is not None:
            file_record.description = description
        
        db.commit()
        
        # 记录操作日志
        await log_operation(
            db=db,
            operation_type="UPDATE_FILE",
            operation_detail=f"更新文件信息：{file_record.original_filename}"
        )
        
        return {"message": "文件信息更新成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新文件信息失败：{str(e)}")

@router.delete("/{file_id}")
async def delete_file(file_id: int, db: Session = Depends(get_db)):
    """删除文件"""
    try:
        file_record = db.query(FileRecord).filter(FileRecord.id == file_id).first()
        
        if not file_record:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 删除物理文件
        if os.path.exists(file_record.file_path):
            os.remove(file_record.file_path)
        
        # 删除数据库记录
        db.delete(file_record)
        db.commit()
        
        # 记录操作日志
        await log_operation(
            db=db,
            operation_type="DELETE_FILE",
            operation_detail=f"删除文件：{file_record.original_filename}"
        )
        
        return {"message": "文件删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除文件失败：{str(e)}")

@router.get("/business/{business_id}", response_model=List[FileRecordResponse])
async def get_files_by_business(
    business_id: str,
    db: Session = Depends(get_db)
):
    """根据业务ID获取关联文件"""
    try:
        files = db.query(FileRecord).filter(
            FileRecord.business_id == business_id
        ).order_by(FileRecord.created_at.desc()).all()
        
        return [
            FileRecordResponse(
                id=file.id,
                filename=file.filename,
                original_filename=file.original_filename,
                file_size=file.file_size,
                file_type=file.file_type,
                category=file.category,
                business_id=file.business_id,
                description=file.description,
                created_at=file.created_at
            )
            for file in files
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取关联文件失败：{str(e)}")