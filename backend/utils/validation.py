import re
from typing import Optional, List, Dict, Any
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)

def validate_id_card(id_card: str) -> bool:
    """验证身份证号码格式"""
    if not id_card:
        return False
    
    # 移除空格
    id_card = id_card.strip().upper()
    
    # 18位身份证号码正则表达式
    pattern = r'^[1-9]\d{5}(18|19|20)\d{2}((0[1-9])|(1[0-2]))(([0-2][1-9])|10|20|30|31)\d{3}[0-9Xx]$'
    
    if not re.match(pattern, id_card):
        return False
    
    # 验证校验码
    return validate_id_card_checksum(id_card)

def validate_id_card_checksum(id_card: str) -> bool:
    """验证身份证号码校验码"""
    try:
        # 权重因子
        weights = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
        # 校验码对应表
        check_codes = ['1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2']
        
        # 计算校验码
        sum_value = 0
        for i in range(17):
            sum_value += int(id_card[i]) * weights[i]
        
        remainder = sum_value % 11
        expected_check_code = check_codes[remainder]
        
        return id_card[17] == expected_check_code
    except (ValueError, IndexError):
        return False

def validate_phone(phone: str) -> bool:
    """验证手机号码格式"""
    if not phone:
        return False
    
    # 移除空格和特殊字符
    phone = re.sub(r'[\s\-\(\)]', '', phone)
    
    # 中国大陆手机号码正则表达式
    pattern = r'^1[3-9]\d{9}$'
    
    return bool(re.match(pattern, phone))

def validate_email(email: str) -> bool:
    """验证邮箱格式"""
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_bank_card(bank_card: str) -> bool:
    """验证银行卡号格式"""
    if not bank_card:
        return False
    
    # 移除空格
    bank_card = re.sub(r'\s', '', bank_card)
    
    # 银行卡号通常为16-19位数字
    if not re.match(r'^\d{16,19}$', bank_card):
        return False
    
    # Luhn算法验证
    return validate_luhn(bank_card)

def validate_luhn(card_number: str) -> bool:
    """Luhn算法验证银行卡号"""
    try:
        digits = [int(d) for d in card_number]
        
        # 从右到左，每隔一位数字乘以2
        for i in range(len(digits) - 2, -1, -2):
            digits[i] *= 2
            if digits[i] > 9:
                digits[i] -= 9
        
        # 所有数字求和
        total = sum(digits)
        
        # 如果总和能被10整除，则验证通过
        return total % 10 == 0
    except (ValueError, TypeError):
        return False

def validate_chinese_name(name: str) -> bool:
    """验证中文姓名格式"""
    if not name:
        return False
    
    name = name.strip()
    
    # 中文姓名正则表达式（2-10个中文字符，可包含·）
    pattern = r'^[\u4e00-\u9fa5·]{2,10}$'
    
    return bool(re.match(pattern, name))

def validate_amount(amount: Any) -> bool:
    """验证金额格式"""
    try:
        if isinstance(amount, str):
            # 移除货币符号和空格
            amount = re.sub(r'[¥$€£\s,]', '', amount)
            amount = float(amount)
        elif not isinstance(amount, (int, float)):
            return False
        
        # 金额必须为非负数，且不超过1亿
        return 0 <= amount <= 100000000
    except (ValueError, TypeError):
        return False

def validate_date_string(date_string: str, format_string: str = '%Y-%m-%d') -> bool:
    """验证日期字符串格式"""
    try:
        datetime.strptime(date_string, format_string)
        return True
    except (ValueError, TypeError):
        return False

def validate_file_extension(filename: str, allowed_extensions: List[str]) -> bool:
    """验证文件扩展名"""
    if not filename:
        return False
    
    file_ext = filename.lower().split('.')[-1]
    return f'.{file_ext}' in [ext.lower() for ext in allowed_extensions]

def validate_file_size(file_size: int, max_size: int) -> bool:
    """验证文件大小"""
    return 0 < file_size <= max_size

class DataValidator:
    """数据验证器类"""
    
    @staticmethod
    def validate_employee_data(data: Dict[str, Any]) -> Dict[str, List[str]]:
        """验证员工数据"""
        errors = {}
        
        # 验证姓名
        if 'name' in data:
            if not data['name'] or not data['name'].strip():
                errors.setdefault('name', []).append('姓名不能为空')
            elif not validate_chinese_name(data['name']):
                errors.setdefault('name', []).append('姓名格式不正确')
        
        # 验证身份证
        if 'id_card' in data:
            if not data['id_card']:
                errors.setdefault('id_card', []).append('身份证号不能为空')
            elif not validate_id_card(data['id_card']):
                errors.setdefault('id_card', []).append('身份证号格式不正确')
        
        # 验证手机号
        if 'phone' in data:
            if not data['phone']:
                errors.setdefault('phone', []).append('手机号不能为空')
            elif not validate_phone(data['phone']):
                errors.setdefault('phone', []).append('手机号格式不正确')
        
        # 验证银行卡号（可选）
        if 'bank_card' in data and data['bank_card']:
            if not validate_bank_card(data['bank_card']):
                errors.setdefault('bank_card', []).append('银行卡号格式不正确')
        
        # 验证开户行（可选）
        if 'bank_name' in data and data['bank_name']:
            if len(data['bank_name'].strip()) < 2:
                errors.setdefault('bank_name', []).append('开户行名称至少2个字符')
        
        return errors
    
    @staticmethod
    def validate_salary_data(data: Dict[str, Any]) -> Dict[str, List[str]]:
        """验证工资数据"""
        errors = {}
        
        # 验证员工ID
        if 'employee_id' not in data or not isinstance(data['employee_id'], int):
            errors.setdefault('employee_id', []).append('员工ID必须为整数')
        
        # 验证工资金额
        if 'salary_amount' not in data:
            errors.setdefault('salary_amount', []).append('工资金额不能为空')
        elif not validate_amount(data['salary_amount']):
            errors.setdefault('salary_amount', []).append('工资金额格式不正确')
        
        # 验证奖金（可选）
        if 'bonus' in data and data['bonus'] is not None:
            if not validate_amount(data['bonus']):
                errors.setdefault('bonus', []).append('奖金金额格式不正确')
        
        # 验证扣款（可选）
        if 'deduction' in data and data['deduction'] is not None:
            if not validate_amount(data['deduction']):
                errors.setdefault('deduction', []).append('扣款金额格式不正确')
        
        # 验证发放日期（可选）
        if 'pay_date' in data and data['pay_date']:
            if isinstance(data['pay_date'], str):
                if not validate_date_string(data['pay_date']):
                    errors.setdefault('pay_date', []).append('发放日期格式不正确')
        
        return errors
    
    @staticmethod
    def validate_expense_data(data: Dict[str, Any]) -> Dict[str, List[str]]:
        """验证支出数据"""
        errors = {}
        
        # 验证项目名称
        if 'project_name' not in data or not data['project_name']:
            errors.setdefault('project_name', []).append('项目名称不能为空')
        elif len(data['project_name'].strip()) < 2:
            errors.setdefault('project_name', []).append('项目名称至少2个字符')
        
        # 验证支出类型
        if 'expense_type' not in data or not data['expense_type']:
            errors.setdefault('expense_type', []).append('支出类型不能为空')
        
        # 验证支出金额
        if 'amount' not in data:
            errors.setdefault('amount', []).append('支出金额不能为空')
        elif not validate_amount(data['amount']) or data['amount'] <= 0:
            errors.setdefault('amount', []).append('支出金额必须大于0')
        
        # 验证支出日期
        if 'expense_date' not in data:
            errors.setdefault('expense_date', []).append('支出日期不能为空')
        elif isinstance(data['expense_date'], str):
            if not validate_date_string(data['expense_date']):
                errors.setdefault('expense_date', []).append('支出日期格式不正确')
        
        return errors
    
    @staticmethod
    def validate_file_upload(filename: str, file_size: int, allowed_extensions: List[str], max_size: int) -> Dict[str, List[str]]:
        """验证文件上传"""
        errors = {}
        
        # 验证文件名
        if not filename:
            errors.setdefault('filename', []).append('文件名不能为空')
        elif not validate_file_extension(filename, allowed_extensions):
            errors.setdefault('filename', []).append(f'不支持的文件类型，支持的类型：{", ".join(allowed_extensions)}')
        
        # 验证文件大小
        if not validate_file_size(file_size, max_size):
            errors.setdefault('file_size', []).append(f'文件大小超过限制：{max_size / 1024 / 1024:.1f}MB')
        
        return errors

def sanitize_input(input_string: str) -> str:
    """清理输入字符串，防止XSS攻击"""
    if not input_string:
        return ''
    
    # 移除HTML标签
    input_string = re.sub(r'<[^>]+>', '', input_string)
    
    # 移除JavaScript代码
    input_string = re.sub(r'javascript:', '', input_string, flags=re.IGNORECASE)
    
    # 移除SQL注入关键词
    sql_keywords = ['select', 'insert', 'update', 'delete', 'drop', 'union', 'exec']
    for keyword in sql_keywords:
        input_string = re.sub(f'\\b{keyword}\\b', '', input_string, flags=re.IGNORECASE)
    
    return input_string.strip()

def validate_pagination(skip: int, limit: int, max_limit: int = 1000) -> Dict[str, Any]:
    """验证分页参数"""
    errors = []
    
    if skip < 0:
        errors.append('skip参数不能为负数')
        skip = 0
    
    if limit <= 0:
        errors.append('limit参数必须大于0')
        limit = 10
    elif limit > max_limit:
        errors.append(f'limit参数不能超过{max_limit}')
        limit = max_limit
    
    return {
        'skip': skip,
        'limit': limit,
        'errors': errors
    }

def validate_search_query(query: str, min_length: int = 1, max_length: int = 100) -> bool:
    """验证搜索查询字符串"""
    if not query:
        return False
    
    query = query.strip()
    
    if len(query) < min_length or len(query) > max_length:
        return False
    
    # 检查是否包含危险字符
    dangerous_chars = ['<', '>', '"', "'", '&', ';']
    for char in dangerous_chars:
        if char in query:
            return False
    
    return True