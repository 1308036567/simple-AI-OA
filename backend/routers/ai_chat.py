from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import json
import uuid
from datetime import datetime

from database import get_db
from models import AIChat, Employee, AccountTable, OperationLog
from schemas.ai_chat import ChatRequest, ChatResponse, VoiceRequest
from utils.ai_model import AIModelManager
from utils.voice_recognition import VoiceRecognizer
from utils.command_parser import CommandParser
from utils.logger import log_operation
from config import settings

router = APIRouter()

# 初始化AI组件
ai_model = AIModelManager(settings.AI_MODEL_PATH)
voice_recognizer = VoiceRecognizer(settings.VOSK_MODEL_PATH)
command_parser = CommandParser()

@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(
    chat_request: ChatRequest,
    db: Session = Depends(get_db)
):
    """与AI进行文本对话"""
    try:
        session_id = chat_request.session_id or str(uuid.uuid4())
        user_input = chat_request.message
        
        # 解析用户指令
        parsed_command = await command_parser.parse_command(user_input)
        
        # 执行指令或生成回复
        if parsed_command["type"] == "command":
            # 执行具体指令
            execution_result = await execute_command(parsed_command, db)
            ai_response = f"已执行指令：{parsed_command['action']}\n结果：{execution_result['message']}"
        else:
            # 普通对话
            ai_response = await ai_model.generate_response(user_input)
            execution_result = None
        
        # 保存对话记录
        chat_record = AIChat(
            session_id=session_id,
            user_input=user_input,
            user_input_type="text",
            ai_response=ai_response,
            command_type=parsed_command.get("type"),
            execution_result=json.dumps(execution_result) if execution_result else None
        )
        
        db.add(chat_record)
        db.commit()
        
        # 记录操作日志
        await log_operation(
            db=db,
            operation_type="AI_CHAT",
            operation_detail=f"AI对话：{user_input[:50]}..."
        )
        
        return ChatResponse(
            session_id=session_id,
            message=ai_response,
            command_type=parsed_command.get("type"),
            execution_result=execution_result,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"AI对话失败：{str(e)}")

@router.post("/voice", response_model=ChatResponse)
async def voice_chat(
    audio_file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """语音对话"""
    try:
        # 验证音频文件格式
        if not audio_file.filename.endswith(('.wav', '.mp3', '.m4a')):
            raise HTTPException(status_code=400, detail="不支持的音频格式")
        
        # 读取音频文件
        audio_content = await audio_file.read()
        
        # 语音识别
        recognized_text = await voice_recognizer.recognize(audio_content)
        
        if not recognized_text:
            raise HTTPException(status_code=400, detail="语音识别失败")
        
        # 创建文本对话请求
        chat_request = ChatRequest(
            message=recognized_text,
            session_id=session_id
        )
        
        # 调用文本对话接口
        response = await chat_with_ai(chat_request, db)
        
        # 更新记录类型为语音
        chat_record = db.query(AIChat).filter(
            AIChat.session_id == response.session_id
        ).order_by(AIChat.created_at.desc()).first()
        
        if chat_record:
            chat_record.user_input_type = "voice"
            db.commit()
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"语音对话失败：{str(e)}")

@router.get("/history/{session_id}")
async def get_chat_history(
    session_id: str,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """获取对话历史"""
    try:
        chats = db.query(AIChat).filter(
            AIChat.session_id == session_id
        ).order_by(AIChat.created_at.desc()).offset(skip).limit(limit).all()
        
        return [
            {
                "id": chat.id,
                "user_input": chat.user_input,
                "user_input_type": chat.user_input_type,
                "ai_response": chat.ai_response,
                "command_type": chat.command_type,
                "execution_result": json.loads(chat.execution_result) if chat.execution_result else None,
                "created_at": chat.created_at
            }
            for chat in chats
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取对话历史失败：{str(e)}")

@router.delete("/history/{session_id}")
async def clear_chat_history(
    session_id: str,
    db: Session = Depends(get_db)
):
    """清除对话历史"""
    try:
        db.query(AIChat).filter(AIChat.session_id == session_id).delete()
        db.commit()
        
        # 记录操作日志
        await log_operation(
            db=db,
            operation_type="CLEAR_CHAT_HISTORY",
            operation_detail=f"清除对话历史：{session_id}"
        )
        
        return {"message": "对话历史已清除"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"清除对话历史失败：{str(e)}")

async def execute_command(parsed_command: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """执行解析后的指令"""
    try:
        command_type = parsed_command["type"]
        action = parsed_command["action"]
        params = parsed_command.get("params", {})
        
        if action == "add_employee":
            # 添加员工
            from routers.employees import create_employee
            from schemas.employee import EmployeeCreate
            
            employee_data = EmployeeCreate(
                name=params["name"],
                id_card=params["id_card"],
                phone=params["phone"],
                bank_card=params.get("bank_card"),
                bank_name=params.get("bank_name")
            )
            
            result = await create_employee(employee_data, db)
            return {"message": f"成功添加员工：{params['name']}", "data": result}
            
        elif action == "create_salary_table":
            # 创建工资表
            from routers.accounts import batch_create_salary
            
            # 解析工资数据
            salary_data = []
            for emp_salary in params["employees"]:
                salary_data.append({
                    "name": emp_salary["name"],
                    "amount": emp_salary["amount"],
                    "project_name": params.get("project_name", ""),
                    "bonus": emp_salary.get("bonus", 0),
                    "deduction": emp_salary.get("deduction", 0)
                })
            
            # 创建账表
            from routers.accounts import create_account_table
            from schemas.account import AccountTableCreate
            
            table_data = AccountTableCreate(
                name=f"{params.get('project_name', '项目')}工资表",
                table_type="salary",
                description=f"AI生成的工资表 - {datetime.now().strftime('%Y-%m-%d')}"
            )
            
            table_result = await create_account_table(table_data, db)
            
            # 批量添加工资记录
            result = await batch_create_salary(
                salary_data=json.dumps(salary_data),
                table_id=table_result.id,
                db=db
            )
            
            return {"message": f"成功创建工资表并添加{result['count']}条记录", "table_id": table_result.id}
            
        elif action == "export_employees":
            # 导出员工信息
            from routers.employees import export_employees
            
            file_response = await export_employees(
                include_archived=params.get("include_archived", False),
                search=params.get("search"),
                db=db
            )
            
            return {"message": "员工信息导出成功", "file_path": file_response.path}
            
        elif action == "backup_data":
            # 备份数据
            from utils.backup import BackupManager
            
            backup_manager = BackupManager()
            backup_path = await backup_manager.create_manual_backup()
            
            return {"message": "数据备份成功", "backup_path": backup_path}
            
        else:
            return {"message": f"未知指令：{action}"}
            
    except Exception as e:
        return {"message": f"指令执行失败：{str(e)}"}

@router.get("/commands")
async def get_available_commands():
    """获取可用指令列表"""
    return {
        "commands": [
            {
                "name": "添加员工",
                "pattern": "添加员工{姓名}，身份证{身份证号}，电话{手机号}，银行卡{银行卡号}，开户行{开户行}",
                "example": "添加员工张三，身份证110101199001011234，电话13800138000，银行卡6222021234567890，开户行中国银行"
            },
            {
                "name": "生成工资表",
                "pattern": "生成{项目名称}工资表：{员工姓名} {金额}元",
                "example": "生成项目A工资表：张三 8000元，李四 7500元"
            },
            {
                "name": "导出员工信息",
                "pattern": "导出{条件}员工信息",
                "example": "导出所有员工信息"
            },
            {
                "name": "备份数据",
                "pattern": "备份系统数据",
                "example": "备份系统数据"
            }
        ]
    }

@router.get("/model/status")
async def get_model_status():
    """获取AI模型状态"""
    try:
        status = await ai_model.get_status()
        voice_status = await voice_recognizer.get_status()
        
        return {
            "ai_model": status,
            "voice_recognizer": voice_status,
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模型状态失败：{str(e)}")

@router.post("/model/reload")
async def reload_model():
    """重新加载AI模型"""
    try:
        await ai_model.reload()
        await voice_recognizer.reload()
        
        return {"message": "AI模型重新加载成功"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重新加载模型失败：{str(e)}")