"""AI安全层模块
实现用户输入→大模型解析→中间层校验→数据库执行→结果返回的安全架构
"""

import json
import re
import sqlite3
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import requests
import os

class OperationType(Enum):
    """操作类型枚举"""
    READ = "read"
    WRITE = "write"
    UNKNOWN = "unknown"

@dataclass
class QueryIntent:
    """查询意图数据结构"""
    operation_type: OperationType
    action: str
    parameters: Dict[str, Any]
    confidence: float
    raw_sql: Optional[str] = None
    security_level: str = "normal"

@dataclass
class SecurityValidationResult:
    """安全校验结果"""
    is_valid: bool
    error_message: Optional[str] = None
    sanitized_query: Optional[str] = None
    allowed_fields: Optional[List[str]] = None

class DatabaseSchema:
    """数据库Schema管理"""
    
    # 定义允许查询的表和字段
    ALLOWED_TABLES = {
        'employees': {
            'fields': ['employee_id', 'name', 'position', 'department', 'phone', 'id_card', 'bank_card', 'bank_name', 'status'],
            'sensitive_fields': ['salary', 'password_hash'],  # 敏感字段，不允许直接查询
            'required_conditions': []  # 移除必需的WHERE条件，允许查询所有员工
        },
        'projects': {
            'fields': ['id', 'name', 'description', 'start_date', 'end_date', 'status', 'manager_id'],
            'sensitive_fields': ['budget', 'internal_notes'],
            'required_conditions': []
        },
        'files': {
            'fields': ['id', 'filename', 'upload_date', 'file_size', 'uploader_id'],
            'sensitive_fields': ['file_path', 'access_token'],
            'required_conditions': []
        },
        'expenses': {
            'fields': ['id', 'description', 'amount', 'date', 'category'],
            'sensitive_fields': ['approver_notes', 'receipt_path'],
            'required_conditions': []
        }
    }
    
    @classmethod
    def get_table_schema(cls, table_name: str) -> Dict[str, Any]:
        """获取表结构信息"""
        return cls.ALLOWED_TABLES.get(table_name, {})
    
    @classmethod
    def get_allowed_fields(cls, table_name: str) -> List[str]:
        """获取允许查询的字段"""
        schema = cls.get_table_schema(table_name)
        return schema.get('fields', [])
    
    @classmethod
    def get_schema_prompt(cls) -> str:
        """生成给大模型的Schema提示"""
        schema_text = "数据库表结构信息：\n"
        for table, info in cls.ALLOWED_TABLES.items():
            schema_text += f"\n表名: {table}\n"
            schema_text += f"可查询字段: {', '.join(info['fields'])}\n"
            if info['required_conditions']:
                schema_text += f"必须包含的条件字段: {', '.join(info['required_conditions'])}\n"
        return schema_text

class AIIntentAnalyzer:
    """AI意图分析器"""
    
    def __init__(self, api_key: str, api_url: str):
        self.api_key = api_key
        self.api_url = api_url
    
    def analyze_intent(self, user_message: str) -> Tuple[QueryIntent, Optional[str]]:
        """分析用户意图"""
        try:
            # 检测简单问候语和闲聊
            greeting_keywords = ['你好', '您好', '嗨', 'hi', 'hello', '谢谢', '再见', '拜拜']
            user_message_lower = user_message.lower().strip()
            print(f"[DEBUG] 检测问候语，用户消息: {repr(user_message_lower)}")
            
            for keyword in greeting_keywords:
                if keyword in user_message_lower:
                    print(f"[DEBUG] 匹配到问候语关键词: {keyword}")
                    if len(user_message.strip()) < 10:
                        return QueryIntent(
                            operation_type=OperationType.UNKNOWN,
                            action="greeting",
                            parameters={},
                            confidence=0.9,
                            security_level="normal"
                        ), None
            
            # 首先进行关键词预检测
            write_keywords = ['添加', '新增', '创建', '插入', '更新', '修改', '删除', '移除']
            read_keywords = ['查询', '查看', '显示', '获取', '列出', '搜索', '找', '看']
            
            is_write_operation = any(keyword in user_message for keyword in write_keywords)
            is_read_operation = any(keyword in user_message for keyword in read_keywords)
            
            print(f"[DEBUG] 用户消息: {repr(user_message)}")
            print(f"[DEBUG] 写操作关键词检测: {is_write_operation}")
            print(f"[DEBUG] 读操作关键词检测: {is_read_operation}")
            
            # 调试关键词匹配
            for keyword in write_keywords:
                if keyword in user_message:
                    print(f"[DEBUG] 匹配到写操作关键词: {keyword}")
            for keyword in read_keywords:
                if keyword in user_message:
                    print(f"[DEBUG] 匹配到读操作关键词: {keyword}")
            
            # 如果明确检测到写操作关键词，直接处理
            if is_write_operation and not is_read_operation:
                return self._handle_write_operation(user_message), None
            
            # 构建系统提示
            system_prompt = self._build_system_prompt()
            
            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                "temperature": 0.1,  # 降低温度以获得更一致的结果
                "max_tokens": 800
            }
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=15)
            
            if response.status_code == 200:
                ai_response = response.json()
                ai_content = ai_response['choices'][0]['message']['content']
                
                # 添加调试信息
                print(f"[DEBUG] AI原始响应: {ai_content}")
                
                # 解析AI响应
                intent = self._parse_ai_response(ai_content)
                print(f"[DEBUG] 解析后的意图: {intent}")
                return intent, None
            else:
                return None, f"AI API调用失败: {response.status_code}"
                
        except Exception as e:
            return None, f"意图分析失败: {str(e)}"
    
    def _build_system_prompt(self) -> str:
        """构建系统提示"""
        schema_info = DatabaseSchema.get_schema_prompt()
        
        return f"""你是一个安全的数据库查询意图分析器。请仔细分析用户意图！

{schema_info}

**关键：首先判断用户是要查看数据还是修改数据！**

如果用户想要查看/获取数据（包含：查询、查看、显示、获取、列出、搜索、找、看等词），使用read操作：
{{
    "operation_type": "read",
    "action": "select_data",
    "parameters": {{
        "table": "表名",
        "fields": ["字段1", "字段2"],
        "conditions": {{}},
        "limit": 50
    }},
    "confidence": 0.95,
    "security_level": "normal"
}}

如果用户想要修改数据（包含：添加、新增、创建、插入、更新、修改、删除、移除等词），使用write操作：
{{
    "operation_type": "write",
    "action": "具体操作名称",
    "parameters": {{
        "target_table": "表名",
        "data": {{
            "字段名": "值"
        }}
    }},
    "confidence": 0.95,
    "security_level": "high"
}}

写操作action映射：
- 添加员工/新增员工/创建员工 → add_employee
- 更新员工/修改员工信息 → update_employee
- 添加项目/新增项目 → add_project
- 更新项目/修改项目 → update_project
- 添加费用/新增费用 → add_expense

**重要示例：**
用户说："添加一个新员工，姓名张三，职位开发工程师"
正确回复：
{{
    "operation_type": "write",
    "action": "add_employee",
    "parameters": {{
        "target_table": "employees",
        "data": {{
            "name": "张三",
            "position": "开发工程师"
        }}
    }},
    "confidence": 0.95,
    "security_level": "high"
}}

用户说："查询所有员工信息"
正确回复：
{{
    "operation_type": "read",
    "action": "select_data",
    "parameters": {{
        "table": "employees",
        "fields": ["*"],
        "conditions": {{}},
        "limit": 50
    }},
    "confidence": 0.95,
    "security_level": "normal"
}}

用户说："查询产品部的所有员工"
正确回复：
{{
    "operation_type": "read",
    "action": "select_data",
    "parameters": {{
        "table": "employees",
        "fields": ["*"],
        "conditions": {{"department": "产品部"}},
        "limit": 50
    }},
    "confidence": 0.95,
    "security_level": "normal"
}}

请严格按照JSON格式回复，不要包含其他内容。"""
    
    def _parse_ai_response(self, ai_content: str) -> QueryIntent:
        """解析AI响应"""
        try:
            data = json.loads(ai_content)
            
            operation_type = OperationType(data.get('operation_type', 'unknown'))
            action = data.get('action', '')
            parameters = data.get('parameters', {})
            confidence = data.get('confidence', 0.0)
            security_level = data.get('security_level', 'normal')
            
            return QueryIntent(
                operation_type=operation_type,
                action=action,
                parameters=parameters,
                confidence=confidence,
                security_level=security_level
            )
            
        except (json.JSONDecodeError, ValueError) as e:
            # 如果解析失败，返回未知操作
            return QueryIntent(
                operation_type=OperationType.UNKNOWN,
                action="unknown",
                parameters={},
                confidence=0.0
            )
    
    def _handle_write_operation(self, user_message: str) -> QueryIntent:
        """直接处理写操作"""
        # 检测具体的写操作类型
        if '添加' in user_message or '新增' in user_message or '创建' in user_message:
            if '员工' in user_message:
                # 提取员工信息
                data = {}
                if '姓名' in user_message:
                    # 简单的姓名提取
                    parts = user_message.split('姓名')
                    if len(parts) > 1:
                        name_part = parts[1].split('，')[0].split(',')[0].strip()
                        data['name'] = name_part
                if '职位' in user_message:
                    # 简单的职位提取
                    parts = user_message.split('职位')
                    if len(parts) > 1:
                        position_part = parts[1].split('，')[0].split(',')[0].strip()
                        data['position'] = position_part
                if '部门' in user_message:
                    # 简单的部门提取
                    parts = user_message.split('部门')
                    if len(parts) > 1:
                        department_part = parts[1].split('，')[0].split(',')[0].strip()
                        data['department'] = department_part
                else:
                    # 如果没有明确指定部门，设置默认部门
                    data['department'] = "技术部"
                
                return QueryIntent(
                    operation_type=OperationType.WRITE,
                    action="add_employee",
                    parameters={
                        "target_table": "employees",
                        "data": data
                    },
                    confidence=0.95,
                    security_level="high"
                )
        elif '更新员工' in user_message:
            action = 'update_employee'
            # 提取员工更新信息
            data = {}
            # 提取员工姓名
            import re
            name_match = re.search(r'员工([\u4e00-\u9fa5]{2,4})(?:的|，)', user_message)
            if name_match:
                data['name'] = name_match.group(1)
            
            # 提取职位信息
            if '职位' in user_message:
                position_match = re.search(r'职位为([\u4e00-\u9fa5]+)', user_message)
                if position_match:
                    data['position'] = position_match.group(1)
            
            return QueryIntent(
                operation_type=OperationType.WRITE,
                action=action,
                parameters={
                    "target_table": "employees",
                    "data": data
                },
                confidence=0.95,
                security_level="high"
            )
            
        elif '删除员工' in user_message:
            action = 'delete_employee'
            # 提取员工删除信息
            data = {}
            # 提取员工姓名
            import re
            name_match = re.search(r'员工([\u4e00-\u9fa5]{2,4})', user_message)
            if name_match:
                data['name'] = name_match.group(1)
            
            return QueryIntent(
                operation_type=OperationType.WRITE,
                action=action,
                parameters={
                    "target_table": "employees",
                    "data": data
                },
                confidence=0.95,
                security_level="high"
            )
        
        # 默认返回未知操作
        return QueryIntent(
            operation_type=OperationType.UNKNOWN,
            action="unknown",
            parameters={},
            confidence=0.0
        )

class SecurityValidator:
    """安全校验器"""
    
    def validate_read_operation(self, intent: QueryIntent) -> SecurityValidationResult:
        """校验读操作"""
        if intent.operation_type != OperationType.READ:
            return SecurityValidationResult(False, "不是读操作")
        
        params = intent.parameters
        table = params.get('table', '')
        fields = params.get('fields', [])
        
        # 检查表是否允许
        if table not in DatabaseSchema.ALLOWED_TABLES:
            return SecurityValidationResult(False, f"不允许访问表: {table}")
        
        # 检查字段是否允许
        allowed_fields = DatabaseSchema.get_allowed_fields(table)
        
        # 如果字段包含 "*"，替换为所有允许的字段
        if '*' in fields:
            fields = allowed_fields
        else:
            for field in fields:
                if field not in allowed_fields:
                    return SecurityValidationResult(False, f"不允许访问字段: {field}")
        
        # 检查是否包含必需的条件
        schema = DatabaseSchema.get_table_schema(table)
        required_conditions = schema.get('required_conditions', [])
        conditions = params.get('conditions', {})
        
        for required_field in required_conditions:
            if required_field not in conditions:
                return SecurityValidationResult(False, f"缺少必需的查询条件: {required_field}")
        
        # 生成安全的查询
        sanitized_query = self._build_safe_query(table, fields, conditions, params.get('limit'))
        
        return SecurityValidationResult(
            True, 
            sanitized_query=sanitized_query,
            allowed_fields=fields
        )
    
    def validate_write_operation(self, intent: QueryIntent) -> SecurityValidationResult:
        """校验写操作"""
        if intent.operation_type != OperationType.WRITE:
            return SecurityValidationResult(False, "不是写操作")
        
        # 检查是否是预定义的安全操作
        allowed_actions = [
            'add_employee', 'update_employee', 'delete_employee',
            'add_project', 'update_project',
            'add_expense'
        ]
        
        if intent.action not in allowed_actions:
            return SecurityValidationResult(False, f"不允许的写操作: {intent.action}")
        
        return SecurityValidationResult(True)
    
    def _build_safe_query(self, table: str, fields: List[str], conditions: Dict[str, Any], limit: Optional[int]) -> str:
        """构建安全的SQL查询"""
        # 构建SELECT子句
        if not fields:
            allowed_fields = DatabaseSchema.get_allowed_fields(table)
            fields = allowed_fields
        
        select_clause = f"SELECT {', '.join(fields)}"
        from_clause = f"FROM {table}"
        
        # 构建WHERE子句
        where_conditions = []
        for field, value in conditions.items():
            # 简单的参数化查询（实际实现中应使用更严格的参数绑定）
            where_conditions.append(f"{field} = ?")
        
        where_clause = ""
        if where_conditions:
            where_clause = f"WHERE {' AND '.join(where_conditions)}"
        
        # 构建LIMIT子句
        limit_clause = ""
        if limit and isinstance(limit, int) and limit > 0:
            limit_clause = f"LIMIT {min(limit, 1000)}"  # 最大限制1000条
        
        query = f"{select_clause} {from_clause} {where_clause} {limit_clause}".strip()
        return query

class SecureWriteOperations:
    """安全写操作接口"""
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    def add_employee(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """安全添加员工"""
        try:
            # 数据验证
            required_fields = ['name', 'position', 'department']
            for field in required_fields:
                if field not in data:
                    return False, f"缺少必需字段: {field}"
            
            # 手机号格式验证
            if 'phone' in data:
                phone = data['phone']
                if not re.match(r'^1[3-9]\d{9}$', phone):
                    return False, "手机号格式不正确"
            
            # 邮箱格式验证
            if 'email' in data:
                email = data['email']
                if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
                    return False, "邮箱格式不正确"
            
            # 只允许插入安全字段，并生成员工ID和银行卡号
            import random
            employee_id = f"EMP{random.randint(1000, 9999)}"
            bank_card = f"622202{random.randint(1000000000, 9999999999)}"
            
            safe_data = {
                'employee_id': employee_id,
                'name': data.get('name', ''),
                'id_card': data.get('id_card', ''),
                'phone': data.get('phone', ''),
                'bank_card': bank_card,
                'bank_name': data.get('bank_name', '中国银行'),  # 默认银行
                'position': data.get('position', ''),
                'department': data.get('department', '技术部'),  # 默认部门
                'status': '在职'  # 默认状态
            }
            
            # 调用数据库插入
            result = self.db.add_employee(safe_data)
            return True, "员工添加成功"
            
        except Exception as e:
            return False, f"添加员工失败: {str(e)}"
    
    def update_employee(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """安全更新员工信息"""
        try:
            employee_id = None
            
            # 如果提供了员工ID，直接使用
            if 'id' in data:
                employee_id = data['id']
            # 如果提供了姓名，通过姓名查找员工ID
            elif 'name' in data:
                employees = self.db.get_all_employees()
                for emp in employees:
                    if emp['name'] == data['name']:
                        employee_id = emp['employee_id']
                        break
                
                if not employee_id:
                    return False, f"未找到姓名为 {data['name']} 的员工"
            else:
                return False, "缺少员工ID或姓名"
            
            # 获取现有员工信息
            existing_employee = None
            employees = self.db.get_all_employees()
            for emp in employees:
                if emp['employee_id'] == employee_id:
                    existing_employee = emp
                    break
            
            if not existing_employee:
                return False, "员工不存在"
            
            # 只允许更新安全字段，保留原有值
            safe_data = {
                'name': existing_employee['name'],
                'id_card': existing_employee['id_card'],
                'phone': existing_employee['phone'],
                'bank_card': existing_employee['bank_card'],
                'bank_name': existing_employee['bank_name'],
                'position': data.get('position', existing_employee['position']),
                'department': data.get('department', existing_employee['department']),
                'status': data.get('status', existing_employee['status'])
            }
            
            # 调用数据库更新
            result = self.db.update_employee(employee_id, safe_data)
            return True, "员工信息更新成功"
            
        except Exception as e:
            return False, f"更新员工信息失败: {str(e)}"
    
    def delete_employee(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """安全删除员工"""
        try:
            employee_id = None
            
            # 如果提供了姓名，先查找员工ID
            if 'name' in data:
                employees = self.db.get_all_employees()
                for emp in employees:
                    if emp['name'] == data['name']:
                        employee_id = emp['employee_id']
                        break
                
                if not employee_id:
                    return False, f"未找到姓名为 {data['name']} 的员工"
            elif 'employee_id' in data:
                employee_id = data['employee_id']
            else:
                return False, "缺少员工ID或姓名"
            
            # 调用数据库删除
            result = self.db.delete_employee(employee_id)
            return True, "员工删除成功"
            
        except Exception as e:
            return False, f"删除员工失败: {str(e)}"
    
    def add_project(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """安全添加项目"""
        try:
            required_fields = ['name', 'description']
            for field in required_fields:
                if field not in data:
                    return False, f"缺少必需字段: {field}"
            
            safe_fields = ['name', 'description', 'start_date', 'end_date', 'manager_id']
            safe_data = {k: v for k, v in data.items() if k in safe_fields}
            safe_data['status'] = '进行中'  # 默认状态
            
            result = self.db.add_project(safe_data)
            return True, "项目添加成功"
            
        except Exception as e:
            return False, f"添加项目失败: {str(e)}"
    
    def add_expense(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """安全添加费用记录"""
        try:
            required_fields = ['description', 'amount', 'category']
            for field in required_fields:
                if field not in data:
                    return False, f"缺少必需字段: {field}"
            
            # 金额验证
            try:
                amount = float(data['amount'])
                if amount <= 0:
                    return False, "金额必须大于0"
            except ValueError:
                return False, "金额格式不正确"
            
            safe_fields = ['description', 'amount', 'category']
            safe_data = {k: v for k, v in data.items() if k in safe_fields}
            safe_data['date'] = datetime.now().strftime('%Y-%m-%d')
            
            result = self.db.add_expense(safe_data)
            return True, "费用记录添加成功"
            
        except Exception as e:
            return False, f"添加费用记录失败: {str(e)}"

class AISecurityLayer:
    """AI安全层主类"""
    
    def __init__(self, db_manager, api_key: str, api_url: str):
        self.db = db_manager
        self.intent_analyzer = AIIntentAnalyzer(api_key, api_url)
        self.security_validator = SecurityValidator()
        self.write_operations = SecureWriteOperations(db_manager)
    
    def process_user_query(self, user_message: str) -> Dict[str, Any]:
        """处理用户查询的主入口"""
        try:
            # 第一步：AI意图分析
            intent, error = self.intent_analyzer.analyze_intent(user_message)
            if error:
                return {
                    "success": False,
                    "message": f"意图分析失败: {error}",
                    "data": None
                }
            
            if intent.operation_type == OperationType.READ:
                return self._handle_read_operation(intent)
            elif intent.operation_type == OperationType.WRITE:
                return self._handle_write_operation(intent)
            elif intent.action == "greeting":
                return {
                    "success": True,
                    "message": "您好！我是您的AI助手，可以帮您查询员工信息、项目数据、财务记录等。请问有什么可以帮助您的吗？",
                    "data": None
                }
            else:
                return {
                    "success": False,
                    "message": "抱歉，我无法理解您的请求。您可以尝试询问员工信息、项目数据或财务记录等。",
                    "data": None
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"处理查询时发生错误: {str(e)}",
                "data": None
            }
    
    def _handle_read_operation(self, intent: QueryIntent) -> Dict[str, Any]:
        """处理读操作"""
        # 第二步：安全校验
        validation_result = self.security_validator.validate_read_operation(intent)
        if not validation_result.is_valid:
            return {
                "success": False,
                "message": f"安全校验失败: {validation_result.error_message}",
                "data": None
            }
        
        # 第三步：执行安全查询
        try:
            # 使用构建的安全查询和条件
            query = validation_result.sanitized_query
            conditions = intent.parameters.get('conditions', {})
            
            # 提取条件值用于参数化查询
            condition_values = list(conditions.values())
            
            # 执行参数化查询
            if condition_values:
                data = self.db.execute_query(query, tuple(condition_values))
            else:
                data = self.db.execute_query(query)
            
            # 第四步：生成自然语言回复
            natural_response = self._generate_natural_response(intent, data)
            
            return {
                "success": True,
                "message": natural_response,
                "data": data,
                "query_info": {
                    "intent": intent.action,
                    "confidence": intent.confidence,
                    "security_level": intent.security_level
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"执行查询失败: {str(e)}",
                "data": None
            }
    
    def _handle_write_operation(self, intent: QueryIntent) -> Dict[str, Any]:
        """处理写操作"""
        # 第二步：安全校验
        validation_result = self.security_validator.validate_write_operation(intent)
        if not validation_result.is_valid:
            return {
                "success": False,
                "message": f"安全校验失败: {validation_result.error_message}",
                "data": None
            }
        
        # 第三步：执行预定义的安全写操作
        try:
            action = intent.action
            data = intent.parameters.get('data', {})
            
            if action == 'add_employee':
                success, message = self.write_operations.add_employee(data)
            elif action == 'update_employee':
                success, message = self.write_operations.update_employee(data)
            elif action == 'delete_employee':
                success, message = self.write_operations.delete_employee(data)
            elif action == 'add_project':
                success, message = self.write_operations.add_project(data)
            elif action == 'add_expense':
                success, message = self.write_operations.add_expense(data)
            else:
                return {
                    "success": False,
                    "message": f"不支持的写操作: {action}",
                    "data": None
                }
            
            return {
                "success": success,
                "message": message,
                "data": None,
                "operation_info": {
                    "action": action,
                    "confidence": intent.confidence,
                    "security_level": intent.security_level
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"执行写操作失败: {str(e)}",
                "data": None
            }
    
    def _generate_natural_response(self, intent: QueryIntent, data: List[Dict]) -> str:
        """生成自然语言回复"""
        table = intent.parameters.get('table', '')
        count = len(data) if data else 0
        
        if table == 'employees':
            return f"查询到 {count} 条员工信息。"
        elif table == 'projects':
            return f"查询到 {count} 个项目。"
        elif table == 'files':
            return f"查询到 {count} 个文件。"
        elif table == 'expenses':
            return f"查询到 {count} 条费用记录。"
        else:
            return f"查询完成，共 {count} 条记录。"