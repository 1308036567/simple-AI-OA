from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
from config import settings
import logging

logger = logging.getLogger(__name__)

class EncryptionManager:
    """加密管理器"""
    
    def __init__(self):
        self.key = self._get_or_create_key()
        self.cipher = Fernet(self.key)
    
    def _get_or_create_key(self) -> bytes:
        """获取或创建加密密钥"""
        try:
            # 从配置中获取密钥
            if hasattr(settings, 'AES_KEY') and settings.AES_KEY:
                # 使用配置的密钥生成Fernet密钥
                password = settings.AES_KEY.encode()
                salt = b'enterprise_salt_2024'  # 固定盐值，生产环境应该使用随机盐值
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=100000,
                )
                key = base64.urlsafe_b64encode(kdf.derive(password))
                return key
            else:
                # 生成新密钥
                return Fernet.generate_key()
        except Exception as e:
            logger.error(f"密钥生成失败: {e}")
            # 使用默认密钥
            return Fernet.generate_key()
    
    def encrypt(self, data: str) -> bytes:
        """加密数据"""
        try:
            if not data:
                return b''
            return self.cipher.encrypt(data.encode('utf-8'))
        except Exception as e:
            logger.error(f"数据加密失败: {e}")
            raise
    
    def decrypt(self, encrypted_data: bytes) -> str:
        """解密数据"""
        try:
            if not encrypted_data:
                return ''
            decrypted_bytes = self.cipher.decrypt(encrypted_data)
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"数据解密失败: {e}")
            raise
    
    def encrypt_dict(self, data_dict: dict, fields_to_encrypt: list) -> dict:
        """加密字典中的指定字段"""
        result = data_dict.copy()
        for field in fields_to_encrypt:
            if field in result and result[field]:
                result[field] = self.encrypt(str(result[field]))
        return result
    
    def decrypt_dict(self, data_dict: dict, fields_to_decrypt: list) -> dict:
        """解密字典中的指定字段"""
        result = data_dict.copy()
        for field in fields_to_decrypt:
            if field in result and result[field]:
                try:
                    result[field] = self.decrypt(result[field])
                except Exception as e:
                    logger.warning(f"字段 {field} 解密失败: {e}")
                    result[field] = '***解密失败***'
        return result

# 全局加密管理器实例
encryption_manager = EncryptionManager()

def encrypt_sensitive_data(data: str) -> bytes:
    """加密敏感数据"""
    return encryption_manager.encrypt(data)

def decrypt_sensitive_data(encrypted_data: bytes) -> str:
    """解密敏感数据"""
    return encryption_manager.decrypt(encrypted_data)

def mask_sensitive_data(data: str, mask_char: str = '*', show_chars: int = 4) -> str:
    """遮蔽敏感数据显示"""
    if not data or len(data) <= show_chars:
        return mask_char * len(data) if data else ''
    
    if len(data) <= show_chars * 2:
        # 如果数据太短，只显示前几位
        return data[:show_chars//2] + mask_char * (len(data) - show_chars//2)
    else:
        # 显示前后几位，中间用*遮蔽
        return data[:show_chars//2] + mask_char * (len(data) - show_chars) + data[-show_chars//2:]

def validate_encryption_key() -> bool:
    """验证加密密钥是否有效"""
    try:
        test_data = "test_encryption_key"
        encrypted = encrypt_sensitive_data(test_data)
        decrypted = decrypt_sensitive_data(encrypted)
        return decrypted == test_data
    except Exception as e:
        logger.error(f"加密密钥验证失败: {e}")
        return False

def generate_new_key() -> str:
    """生成新的加密密钥"""
    key = Fernet.generate_key()
    return base64.urlsafe_b64encode(key).decode('utf-8')

class SecureDataHandler:
    """安全数据处理器"""
    
    # 需要加密的字段列表
    SENSITIVE_FIELDS = ['id_card', 'bank_card', 'password', 'secret']
    
    @staticmethod
    def process_employee_data(employee_data: dict, encrypt: bool = True) -> dict:
        """处理员工数据的加密/解密"""
        sensitive_fields = ['id_card', 'bank_card']
        
        if encrypt:
            return encryption_manager.encrypt_dict(employee_data, sensitive_fields)
        else:
            return encryption_manager.decrypt_dict(employee_data, sensitive_fields)
    
    @staticmethod
    def mask_employee_data(employee_data: dict) -> dict:
        """遮蔽员工敏感数据用于日志记录"""
        result = employee_data.copy()
        
        if 'id_card' in result and result['id_card']:
            result['id_card'] = mask_sensitive_data(result['id_card'], show_chars=6)
        
        if 'bank_card' in result and result['bank_card']:
            result['bank_card'] = mask_sensitive_data(result['bank_card'], show_chars=8)
        
        return result
    
    @staticmethod
    def is_sensitive_field(field_name: str) -> bool:
        """判断字段是否为敏感字段"""
        return field_name.lower() in [f.lower() for f in SecureDataHandler.SENSITIVE_FIELDS]

# 数据脱敏工具函数
def desensitize_id_card(id_card: str) -> str:
    """身份证号脱敏"""
    if not id_card or len(id_card) < 8:
        return id_card
    return id_card[:6] + '*' * (len(id_card) - 10) + id_card[-4:]

def desensitize_phone(phone: str) -> str:
    """手机号脱敏"""
    if not phone or len(phone) < 7:
        return phone
    return phone[:3] + '*' * 4 + phone[-4:]

def desensitize_bank_card(bank_card: str) -> str:
    """银行卡号脱敏"""
    if not bank_card or len(bank_card) < 8:
        return bank_card
    return bank_card[:4] + '*' * (len(bank_card) - 8) + bank_card[-4:]

def desensitize_name(name: str) -> str:
    """姓名脱敏"""
    if not name:
        return name
    if len(name) == 1:
        return name
    elif len(name) == 2:
        return name[0] + '*'
    else:
        return name[0] + '*' * (len(name) - 2) + name[-1]

# 批量脱敏函数
def desensitize_employee_data(employee_data: dict) -> dict:
    """员工数据批量脱敏"""
    result = employee_data.copy()
    
    if 'name' in result:
        result['name'] = desensitize_name(result['name'])
    
    if 'id_card' in result:
        result['id_card'] = desensitize_id_card(result['id_card'])
    
    if 'phone' in result:
        result['phone'] = desensitize_phone(result['phone'])
    
    if 'bank_card' in result:
        result['bank_card'] = desensitize_bank_card(result['bank_card'])
    
    return result