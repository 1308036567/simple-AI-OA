from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import pandas as pd
import os
from datetime import datetime
import uuid

from database import get_db
from models import Employee, OperationLog
from schemas.employee import EmployeeCreate, EmployeeUpdate, EmployeeResponse, EmployeeImportPreview
from utils.encryption import encrypt_sensitive_data, decrypt_sensitive_data
from utils.validation import validate_id_card, validate_phone
from utils.excel_handler import ExcelHandler
from utils.logger import log_operation
from config import EMPLOYEE_FIELD_MAPPING

router = APIRouter()
excel_handler = ExcelHandler()

@router.post("/", response_model=EmployeeResponse)
async def create_employee(employee: EmployeeCreate, db: Session = Depends(get_db)):
    """创建员工信息"""
    try:
        # 验证身份证和手机号
        if not validate_id_card(employee.id_card):
            raise HTTPException(status_code=400, detail="身份证号格式不正确")
        
        if not validate_phone(employee.phone):
            raise HTTPException(status_code=400, detail="手机号格式不正确")
        
        # 检查身份证号是否已存在
        existing_employee = db.query(Employee).filter(
            Employee.id_card == encrypt_sensitive_data(employee.id_card)
        ).first()
        
        if existing_employee:
            raise HTTPException(status_code=400, detail="该身份证号已存在")
        
        # 创建员工记录
        db_employee = Employee(
            name=employee.name,
            id_card=encrypt_sensitive_data(employee.id_card),
            phone=employee.phone,
            bank_card=encrypt_sensitive_data(employee.bank_card) if employee.bank_card else None,
            bank_name=employee.bank_name
        )
        
        db.add(db_employee)
        db.commit()
        db.refresh(db_employee)
        
        # 记录操作日志
        await log_operation(
            db=db,
            operation_type="CREATE_EMPLOYEE",
            operation_detail=f"创建员工：{employee.name}"
        )
        
        # 返回响应（解密敏感数据）
        return EmployeeResponse(
            id=db_employee.id,
            name=db_employee.name,
            id_card=decrypt_sensitive_data(db_employee.id_card),
            phone=db_employee.phone,
            bank_card=decrypt_sensitive_data(db_employee.bank_card) if db_employee.bank_card else None,
            bank_name=db_employee.bank_name,
            is_archived=db_employee.is_archived,
            created_at=db_employee.created_at,
            updated_at=db_employee.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建员工失败：{str(e)}")

@router.get("/", response_model=List[EmployeeResponse])
async def get_employees(
    skip: int = 0,
    limit: int = 100,
    include_archived: bool = False,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取员工列表"""
    try:
        query = db.query(Employee)
        
        # 是否包含归档员工
        if not include_archived:
            query = query.filter(Employee.is_archived == False)
        
        # 搜索功能
        if search:
            query = query.filter(
                Employee.name.contains(search) |
                Employee.phone.contains(search)
            )
        
        employees = query.offset(skip).limit(limit).all()
        
        # 解密敏感数据并返回
        result = []
        for emp in employees:
            result.append(EmployeeResponse(
                id=emp.id,
                name=emp.name,
                id_card=decrypt_sensitive_data(emp.id_card),
                phone=emp.phone,
                bank_card=decrypt_sensitive_data(emp.bank_card) if emp.bank_card else None,
                bank_name=emp.bank_name,
                is_archived=emp.is_archived,
                created_at=emp.created_at,
                updated_at=emp.updated_at
            ))
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取员工列表失败：{str(e)}")

@router.get("/{employee_id}", response_model=EmployeeResponse)
async def get_employee(employee_id: int, db: Session = Depends(get_db)):
    """获取单个员工信息"""
    try:
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        
        if not employee:
            raise HTTPException(status_code=404, detail="员工不存在")
        
        return EmployeeResponse(
            id=employee.id,
            name=employee.name,
            id_card=decrypt_sensitive_data(employee.id_card),
            phone=employee.phone,
            bank_card=decrypt_sensitive_data(employee.bank_card) if employee.bank_card else None,
            bank_name=employee.bank_name,
            is_archived=employee.is_archived,
            created_at=employee.created_at,
            updated_at=employee.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取员工信息失败：{str(e)}")

@router.put("/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: int,
    employee: EmployeeUpdate,
    db: Session = Depends(get_db)
):
    """更新员工信息"""
    try:
        db_employee = db.query(Employee).filter(Employee.id == employee_id).first()
        
        if not db_employee:
            raise HTTPException(status_code=404, detail="员工不存在")
        
        # 验证更新的数据
        if employee.id_card and not validate_id_card(employee.id_card):
            raise HTTPException(status_code=400, detail="身份证号格式不正确")
        
        if employee.phone and not validate_phone(employee.phone):
            raise HTTPException(status_code=400, detail="手机号格式不正确")
        
        # 更新字段
        update_data = employee.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field in ["id_card", "bank_card"] and value:
                setattr(db_employee, field, encrypt_sensitive_data(value))
            else:
                setattr(db_employee, field, value)
        
        db.commit()
        db.refresh(db_employee)
        
        # 记录操作日志
        await log_operation(
            db=db,
            operation_type="UPDATE_EMPLOYEE",
            operation_detail=f"更新员工：{db_employee.name}"
        )
        
        return EmployeeResponse(
            id=db_employee.id,
            name=db_employee.name,
            id_card=decrypt_sensitive_data(db_employee.id_card),
            phone=db_employee.phone,
            bank_card=decrypt_sensitive_data(db_employee.bank_card) if db_employee.bank_card else None,
            bank_name=db_employee.bank_name,
            is_archived=db_employee.is_archived,
            created_at=db_employee.created_at,
            updated_at=db_employee.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新员工信息失败：{str(e)}")

@router.post("/{employee_id}/archive")
async def archive_employee(employee_id: int, db: Session = Depends(get_db)):
    """归档员工"""
    try:
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        
        if not employee:
            raise HTTPException(status_code=404, detail="员工不存在")
        
        employee.is_archived = True
        db.commit()
        
        # 记录操作日志
        await log_operation(
            db=db,
            operation_type="ARCHIVE_EMPLOYEE",
            operation_detail=f"归档员工：{employee.name}"
        )
        
        return {"message": "员工归档成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"归档员工失败：{str(e)}")

@router.post("/import/preview")
async def preview_import(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """预览Excel导入数据"""
    try:
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="只支持Excel文件")
        
        # 读取Excel文件
        content = await file.read()
        df = pd.read_excel(content)
        
        # 字段映射和预览
        preview_data = excel_handler.preview_employee_import(df, EMPLOYEE_FIELD_MAPPING)
        
        return EmployeeImportPreview(
            total_rows=len(df),
            valid_rows=len(preview_data["valid_data"]),
            invalid_rows=len(preview_data["invalid_data"]),
            field_mapping=preview_data["field_mapping"],
            sample_data=preview_data["valid_data"][:5],  # 显示前5条有效数据
            errors=preview_data["invalid_data"][:10]  # 显示前10条错误数据
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"预览导入失败：{str(e)}")

@router.post("/import")
async def import_employees(
    file: UploadFile = File(...),
    field_mapping: str = Form(...),
    db: Session = Depends(get_db)
):
    """导入员工数据"""
    try:
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="只支持Excel文件")
        
        # 读取Excel文件
        content = await file.read()
        df = pd.read_excel(content)
        
        # 解析字段映射
        import json
        mapping = json.loads(field_mapping)
        
        # 导入数据
        result = await excel_handler.import_employees(df, mapping, db)
        
        # 记录操作日志
        await log_operation(
            db=db,
            operation_type="IMPORT_EMPLOYEES",
            operation_detail=f"导入员工数据：成功{result['success_count']}条，失败{result['error_count']}条"
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入员工数据失败：{str(e)}")

@router.get("/export/excel")
async def export_employees(
    include_archived: bool = False,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """导出员工数据为Excel"""
    try:
        # 获取员工数据
        query = db.query(Employee)
        
        if not include_archived:
            query = query.filter(Employee.is_archived == False)
        
        if search:
            query = query.filter(
                Employee.name.contains(search) |
                Employee.phone.contains(search)
            )
        
        employees = query.all()
        
        # 生成Excel文件
        file_path = await excel_handler.export_employees(employees)
        
        # 记录操作日志
        await log_operation(
            db=db,
            operation_type="EXPORT_EMPLOYEES",
            operation_detail=f"导出员工数据：{len(employees)}条记录"
        )
        
        return FileResponse(
            path=file_path,
            filename=f"员工信息_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出员工数据失败：{str(e)}")