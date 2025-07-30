from fastapi import APIRouter, Depends, HTTPException, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import os
from datetime import datetime
import json

from database import get_db
from models import AccountTable, SalaryRecord, ExpenseRecord, Employee
from schemas.account import (
    AccountTableCreate, AccountTableResponse, 
    SalaryRecordCreate, SalaryRecordResponse,
    ExpenseRecordCreate, ExpenseRecordResponse
)
from utils.excel_handler import ExcelHandler
from utils.chart_generator import ChartGenerator
from utils.logger import log_operation

router = APIRouter()
excel_handler = ExcelHandler()
chart_generator = ChartGenerator()

@router.post("/tables", response_model=AccountTableResponse)
async def create_account_table(
    account_table: AccountTableCreate,
    db: Session = Depends(get_db)
):
    """创建账表"""
    try:
        db_table = AccountTable(
            name=account_table.name,
            table_type=account_table.table_type,
            description=account_table.description
        )
        
        db.add(db_table)
        db.commit()
        db.refresh(db_table)
        
        # 记录操作日志
        await log_operation(
            db=db,
            operation_type="CREATE_ACCOUNT_TABLE",
            operation_detail=f"创建账表：{account_table.name}"
        )
        
        return AccountTableResponse(
            id=db_table.id,
            name=db_table.name,
            table_type=db_table.table_type,
            description=db_table.description,
            file_path=db_table.file_path,
            created_at=db_table.created_at,
            updated_at=db_table.updated_at
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建账表失败：{str(e)}")

@router.get("/tables", response_model=List[AccountTableResponse])
async def get_account_tables(
    skip: int = 0,
    limit: int = 100,
    table_type: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取账表列表"""
    try:
        query = db.query(AccountTable)
        
        # 按类型筛选
        if table_type:
            query = query.filter(AccountTable.table_type == table_type)
        
        # 搜索功能
        if search:
            query = query.filter(
                AccountTable.name.contains(search) |
                AccountTable.description.contains(search)
            )
        
        tables = query.order_by(AccountTable.created_at.desc()).offset(skip).limit(limit).all()
        
        return [
            AccountTableResponse(
                id=table.id,
                name=table.name,
                table_type=table.table_type,
                description=table.description,
                file_path=table.file_path,
                created_at=table.created_at,
                updated_at=table.updated_at
            )
            for table in tables
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取账表列表失败：{str(e)}")

@router.post("/tables/{table_id}/salary", response_model=SalaryRecordResponse)
async def add_salary_record(
    table_id: int,
    salary_record: SalaryRecordCreate,
    db: Session = Depends(get_db)
):
    """添加工资记录"""
    try:
        # 验证账表存在
        table = db.query(AccountTable).filter(AccountTable.id == table_id).first()
        if not table:
            raise HTTPException(status_code=404, detail="账表不存在")
        
        # 验证员工存在
        employee = db.query(Employee).filter(Employee.id == salary_record.employee_id).first()
        if not employee:
            raise HTTPException(status_code=404, detail="员工不存在")
        
        # 计算实际金额
        actual_amount = salary_record.salary_amount + salary_record.bonus - salary_record.deduction
        
        db_salary = SalaryRecord(
            employee_id=salary_record.employee_id,
            account_table_id=table_id,
            project_name=salary_record.project_name,
            salary_amount=salary_record.salary_amount,
            bonus=salary_record.bonus,
            deduction=salary_record.deduction,
            actual_amount=actual_amount,
            pay_date=salary_record.pay_date,
            remark=salary_record.remark
        )
        
        db.add(db_salary)
        db.commit()
        db.refresh(db_salary)
        
        # 记录操作日志
        await log_operation(
            db=db,
            operation_type="ADD_SALARY_RECORD",
            operation_detail=f"添加工资记录：{employee.name} - {salary_record.salary_amount}元"
        )
        
        return SalaryRecordResponse(
            id=db_salary.id,
            employee_id=db_salary.employee_id,
            employee_name=employee.name,
            account_table_id=db_salary.account_table_id,
            project_name=db_salary.project_name,
            salary_amount=db_salary.salary_amount,
            bonus=db_salary.bonus,
            deduction=db_salary.deduction,
            actual_amount=db_salary.actual_amount,
            pay_date=db_salary.pay_date,
            remark=db_salary.remark,
            created_at=db_salary.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"添加工资记录失败：{str(e)}")

@router.post("/tables/{table_id}/expense", response_model=ExpenseRecordResponse)
async def add_expense_record(
    table_id: int,
    expense_record: ExpenseRecordCreate,
    db: Session = Depends(get_db)
):
    """添加支出记录"""
    try:
        # 验证账表存在
        table = db.query(AccountTable).filter(AccountTable.id == table_id).first()
        if not table:
            raise HTTPException(status_code=404, detail="账表不存在")
        
        db_expense = ExpenseRecord(
            account_table_id=table_id,
            project_name=expense_record.project_name,
            expense_type=expense_record.expense_type,
            amount=expense_record.amount,
            expense_date=expense_record.expense_date,
            description=expense_record.description,
            receipt_file_id=expense_record.receipt_file_id
        )
        
        db.add(db_expense)
        db.commit()
        db.refresh(db_expense)
        
        # 记录操作日志
        await log_operation(
            db=db,
            operation_type="ADD_EXPENSE_RECORD",
            operation_detail=f"添加支出记录：{expense_record.project_name} - {expense_record.amount}元"
        )
        
        return ExpenseRecordResponse(
            id=db_expense.id,
            account_table_id=db_expense.account_table_id,
            project_name=db_expense.project_name,
            expense_type=db_expense.expense_type,
            amount=db_expense.amount,
            expense_date=db_expense.expense_date,
            description=db_expense.description,
            receipt_file_id=db_expense.receipt_file_id,
            created_at=db_expense.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"添加支出记录失败：{str(e)}")

@router.get("/tables/{table_id}/salary", response_model=List[SalaryRecordResponse])
async def get_salary_records(
    table_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取工资记录列表"""
    try:
        records = db.query(SalaryRecord, Employee).join(
            Employee, SalaryRecord.employee_id == Employee.id
        ).filter(
            SalaryRecord.account_table_id == table_id
        ).offset(skip).limit(limit).all()
        
        return [
            SalaryRecordResponse(
                id=record.SalaryRecord.id,
                employee_id=record.SalaryRecord.employee_id,
                employee_name=record.Employee.name,
                account_table_id=record.SalaryRecord.account_table_id,
                project_name=record.SalaryRecord.project_name,
                salary_amount=record.SalaryRecord.salary_amount,
                bonus=record.SalaryRecord.bonus,
                deduction=record.SalaryRecord.deduction,
                actual_amount=record.SalaryRecord.actual_amount,
                pay_date=record.SalaryRecord.pay_date,
                remark=record.SalaryRecord.remark,
                created_at=record.SalaryRecord.created_at
            )
            for record in records
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取工资记录失败：{str(e)}")

@router.get("/tables/{table_id}/expense", response_model=List[ExpenseRecordResponse])
async def get_expense_records(
    table_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取支出记录列表"""
    try:
        records = db.query(ExpenseRecord).filter(
            ExpenseRecord.account_table_id == table_id
        ).offset(skip).limit(limit).all()
        
        return [
            ExpenseRecordResponse(
                id=record.id,
                account_table_id=record.account_table_id,
                project_name=record.project_name,
                expense_type=record.expense_type,
                amount=record.amount,
                expense_date=record.expense_date,
                description=record.description,
                receipt_file_id=record.receipt_file_id,
                created_at=record.created_at
            )
            for record in records
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取支出记录失败：{str(e)}")

@router.get("/tables/{table_id}/export/excel")
async def export_account_table(
    table_id: int,
    db: Session = Depends(get_db)
):
    """导出账表为Excel"""
    try:
        # 获取账表信息
        table = db.query(AccountTable).filter(AccountTable.id == table_id).first()
        if not table:
            raise HTTPException(status_code=404, detail="账表不存在")
        
        # 根据账表类型导出不同内容
        if table.table_type == "salary":
            file_path = await excel_handler.export_salary_table(table_id, db)
        elif table.table_type == "expense":
            file_path = await excel_handler.export_expense_table(table_id, db)
        else:
            raise HTTPException(status_code=400, detail="不支持的账表类型")
        
        # 更新账表文件路径
        table.file_path = file_path
        db.commit()
        
        # 记录操作日志
        await log_operation(
            db=db,
            operation_type="EXPORT_ACCOUNT_TABLE",
            operation_detail=f"导出账表：{table.name}"
        )
        
        return FileResponse(
            path=file_path,
            filename=f"{table.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出账表失败：{str(e)}")

@router.get("/tables/{table_id}/chart")
async def generate_chart(
    table_id: int,
    chart_type: str = "bar",
    db: Session = Depends(get_db)
):
    """生成账表图表"""
    try:
        # 获取账表信息
        table = db.query(AccountTable).filter(AccountTable.id == table_id).first()
        if not table:
            raise HTTPException(status_code=404, detail="账表不存在")
        
        # 根据账表类型生成图表
        if table.table_type == "salary":
            chart_path = await chart_generator.generate_salary_chart(table_id, chart_type, db)
        elif table.table_type == "expense":
            chart_path = await chart_generator.generate_expense_chart(table_id, chart_type, db)
        else:
            raise HTTPException(status_code=400, detail="不支持的账表类型")
        
        # 记录操作日志
        await log_operation(
            db=db,
            operation_type="GENERATE_CHART",
            operation_detail=f"生成图表：{table.name} - {chart_type}"
        )
        
        return FileResponse(
            path=chart_path,
            filename=f"{table.name}_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
            media_type="text/html"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成图表失败：{str(e)}")

@router.post("/batch/salary")
async def batch_create_salary(
    salary_data: str = Form(...),
    table_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """批量创建工资记录（AI指令解析）"""
    try:
        # 解析工资数据
        data = json.loads(salary_data)
        
        # 验证账表存在
        table = db.query(AccountTable).filter(AccountTable.id == table_id).first()
        if not table:
            raise HTTPException(status_code=404, detail="账表不存在")
        
        created_records = []
        
        for item in data:
            # 查找员工
            employee = db.query(Employee).filter(Employee.name == item["name"]).first()
            if not employee:
                continue
            
            # 创建工资记录
            salary_record = SalaryRecord(
                employee_id=employee.id,
                account_table_id=table_id,
                project_name=item.get("project_name", ""),
                salary_amount=float(item["amount"]),
                bonus=float(item.get("bonus", 0)),
                deduction=float(item.get("deduction", 0)),
                actual_amount=float(item["amount"]) + float(item.get("bonus", 0)) - float(item.get("deduction", 0)),
                remark=item.get("remark", "")
            )
            
            db.add(salary_record)
            created_records.append(salary_record)
        
        db.commit()
        
        # 记录操作日志
        await log_operation(
            db=db,
            operation_type="BATCH_CREATE_SALARY",
            operation_detail=f"批量创建工资记录：{len(created_records)}条"
        )
        
        return {
            "message": f"成功创建{len(created_records)}条工资记录",
            "count": len(created_records)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"批量创建工资记录失败：{str(e)}")

@router.get("/statistics/{table_id}")
async def get_account_statistics(
    table_id: int,
    db: Session = Depends(get_db)
):
    """获取账表统计信息"""
    try:
        # 获取账表信息
        table = db.query(AccountTable).filter(AccountTable.id == table_id).first()
        if not table:
            raise HTTPException(status_code=404, detail="账表不存在")
        
        statistics = {}
        
        if table.table_type == "salary":
            # 工资统计
            salary_records = db.query(SalaryRecord).filter(
                SalaryRecord.account_table_id == table_id
            ).all()
            
            total_salary = sum(record.salary_amount for record in salary_records)
            total_bonus = sum(record.bonus for record in salary_records)
            total_deduction = sum(record.deduction for record in salary_records)
            total_actual = sum(record.actual_amount for record in salary_records)
            
            statistics = {
                "type": "salary",
                "total_records": len(salary_records),
                "total_salary": total_salary,
                "total_bonus": total_bonus,
                "total_deduction": total_deduction,
                "total_actual": total_actual,
                "average_salary": total_salary / len(salary_records) if salary_records else 0
            }
            
        elif table.table_type == "expense":
            # 支出统计
            expense_records = db.query(ExpenseRecord).filter(
                ExpenseRecord.account_table_id == table_id
            ).all()
            
            total_expense = sum(record.amount for record in expense_records)
            
            # 按类型分组统计
            expense_by_type = {}
            for record in expense_records:
                if record.expense_type not in expense_by_type:
                    expense_by_type[record.expense_type] = 0
                expense_by_type[record.expense_type] += record.amount
            
            statistics = {
                "type": "expense",
                "total_records": len(expense_records),
                "total_expense": total_expense,
                "expense_by_type": expense_by_type,
                "average_expense": total_expense / len(expense_records) if expense_records else 0
            }
        
        return statistics
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败：{str(e)}")