import os
import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, date
import asyncio
import aiohttp
import speech_recognition as sr
import pyttsx3
from io import BytesIO
import wave
import threading
import json
from config import DEEPSEEK_CONFIG, AI_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

class AIModelManager:
    """AI模型管理器 - 使用DeepSeek API"""
    
    def __init__(self):
        self.deepseek_config = DEEPSEEK_CONFIG
        self.system_prompt = AI_SYSTEM_PROMPT
        self.is_model_loaded = True  # API模式下默认可用
        self.model_status = 'loaded'
        self.speech_recognizer = sr.Recognizer()
        self.tts_engine = None
        self._init_tts()
        self.session = None
    
    def _init_tts(self):
        """初始化文本转语音引擎"""
        try:
            self.tts_engine = pyttsx3.init()
            # 设置语音参数
            voices = self.tts_engine.getProperty('voices')
            if voices:
                # 尝试设置中文语音
                for voice in voices:
                    if 'chinese' in voice.name.lower() or 'zh' in voice.id.lower():
                        self.tts_engine.setProperty('voice', voice.id)
                        break
            
            self.tts_engine.setProperty('rate', 150)  # 语速
            self.tts_engine.setProperty('volume', 0.8)  # 音量
        except Exception as e:
            logger.error(f"TTS引擎初始化失败: {e}")
    
    async def load_model(self) -> Dict[str, Any]:
        """初始化DeepSeek API连接"""
        try:
            self.model_status = 'loading'
            
            # 检查API配置
            if not self.deepseek_config.get('api_key') or self.deepseek_config['api_key'] == 'your-deepseek-api-key-here':
                raise Exception("DeepSeek API密钥未配置，请在config.py中设置DEEPSEEK_API_KEY")
            
            # 创建HTTP会话
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.deepseek_config.get('timeout', 30))
            )
            
            # 测试API连接
            await self._test_api_connection()
            
            self.is_model_loaded = True
            self.model_status = 'loaded'
            
            return {
                'success': True,
                'message': 'DeepSeek API连接成功',
                'model_info': {
                    'name': 'DeepSeek Chat',
                    'model': self.deepseek_config.get('model', 'deepseek-chat'),
                    'status': self.model_status,
                    'type': 'api'
                }
            }
        except Exception as e:
            self.model_status = 'error'
            logger.error(f"DeepSeek API初始化失败: {e}")
            return {
                'success': False,
                'message': f'API初始化失败: {str(e)}',
                'model_info': None
            }
    
    async def chat_with_model(self, message: str, context: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """与AI模型对话"""
        try:
            if not self.is_model_loaded:
                return {
                    'success': False,
                    'message': '模型未加载',
                    'response': '抱歉，AI模型尚未加载，请稍后再试。'
                }
            
            # 构建对话上下文
            conversation_context = self._build_context(message, context)
            
            # 检查是否为指令
            instruction_result = self._parse_instruction(message)
            if instruction_result['is_instruction']:
                return {
                    'success': True,
                    'message': '指令识别成功',
                    'response': instruction_result['response'],
                    'instruction': instruction_result['instruction'],
                    'parameters': instruction_result['parameters']
                }
            
            # 模拟AI响应
            response = await self._generate_response(conversation_context)
            
            return {
                'success': True,
                'message': '对话成功',
                'response': response,
                'instruction': None,
                'parameters': None
            }
            
        except Exception as e:
            logger.error(f"AI对话失败: {e}")
            return {
                'success': False,
                'message': f'对话失败: {str(e)}',
                'response': '抱歉，处理您的请求时出现了错误。'
            }
    
    def _build_context(self, message: str, context: List[Dict[str, str]] = None) -> str:
        """构建对话上下文"""
        context_parts = []
        
        # 添加系统提示
        context_parts.append("你是一个专业的企业管理助手，专门帮助处理员工信息、工资管理、支出记录等业务。")
        
        # 添加历史对话
        if context:
            for item in context[-5:]:  # 只保留最近5轮对话
                context_parts.append(f"用户: {item.get('user', '')}")
                context_parts.append(f"助手: {item.get('assistant', '')}")
        
        # 添加当前消息
        context_parts.append(f"用户: {message}")
        context_parts.append("助手: ")
        
        return "\n".join(context_parts)
    
    def _parse_instruction(self, message: str) -> Dict[str, Any]:
        """解析指令"""
        message_lower = message.lower().strip()
        
        # 添加员工指令
        if any(keyword in message_lower for keyword in ['添加员工', '新增员工', '录入员工']):
            return self._parse_add_employee_instruction(message)
        
        # 创建工资表指令
        if any(keyword in message_lower for keyword in ['创建工资表', '生成工资表', '工资表']):
            return self._parse_create_salary_instruction(message)
        
        # 导出数据指令
        if any(keyword in message_lower for keyword in ['导出', '下载', '生成报表']):
            return self._parse_export_instruction(message)
        
        # 备份数据指令
        if any(keyword in message_lower for keyword in ['备份', '备份数据']):
            return {
                'is_instruction': True,
                'instruction': 'backup_data',
                'parameters': {},
                'response': '正在为您备份数据...'
            }
        
        return {
            'is_instruction': False,
            'instruction': None,
            'parameters': None,
            'response': None
        }
    
    def _parse_add_employee_instruction(self, message: str) -> Dict[str, Any]:
        """解析添加员工指令"""
        try:
            # 提取员工信息
            employee_data = {}
            
            # 提取姓名
            name_pattern = r'(?:姓名|叫|名字)[:：]?\s*([\u4e00-\u9fa5·]{2,10})'
            name_match = re.search(name_pattern, message)
            if name_match:
                employee_data['name'] = name_match.group(1)
            
            # 提取身份证号
            id_pattern = r'(?:身份证|身份证号)[:：]?\s*([0-9X]{15,18})'
            id_match = re.search(id_pattern, message)
            if id_match:
                employee_data['id_card'] = id_match.group(1)
            
            # 提取手机号
            phone_pattern = r'(?:手机|电话|手机号)[:：]?\s*(1[3-9]\d{9})'
            phone_match = re.search(phone_pattern, message)
            if phone_match:
                employee_data['phone'] = phone_match.group(1)
            
            # 提取银行卡号
            bank_pattern = r'(?:银行卡|卡号)[:：]?\s*(\d{16,19})'
            bank_match = re.search(bank_pattern, message)
            if bank_match:
                employee_data['bank_card'] = bank_match.group(1)
            
            # 提取开户行
            bank_name_pattern = r'(?:开户行|银行)[:：]?\s*([\u4e00-\u9fa5]{2,20})'
            bank_name_match = re.search(bank_name_pattern, message)
            if bank_name_match:
                employee_data['bank_name'] = bank_name_match.group(1)
            
            if employee_data:
                return {
                    'is_instruction': True,
                    'instruction': 'add_employee',
                    'parameters': employee_data,
                    'response': f"正在为您添加员工信息: {employee_data.get('name', '未知姓名')}"
                }
            else:
                return {
                    'is_instruction': True,
                    'instruction': 'add_employee',
                    'parameters': {},
                    'response': '请提供员工的详细信息，包括姓名、身份证号、手机号等。'
                }
                
        except Exception as e:
            logger.error(f"解析添加员工指令失败: {e}")
            return {
                'is_instruction': False,
                'instruction': None,
                'parameters': None,
                'response': None
            }
    
    def _parse_create_salary_instruction(self, message: str) -> Dict[str, Any]:
        """解析创建工资表指令"""
        try:
            parameters = {}
            
            # 提取项目名称
            project_pattern = r'(?:项目|工程)[:：]?\s*([\u4e00-\u9fa5A-Za-z0-9]{2,20})'
            project_match = re.search(project_pattern, message)
            if project_match:
                parameters['project_name'] = project_match.group(1)
            
            # 提取时间期间
            period_pattern = r'(\d{4}年\d{1,2}月|\d{4}-\d{1,2})'
            period_match = re.search(period_pattern, message)
            if period_match:
                parameters['period'] = period_match.group(1)
            
            # 提取员工工资信息
            salary_pattern = r'([\u4e00-\u9fa5·]{2,10})\s*(\d+)\s*元'
            salary_matches = re.findall(salary_pattern, message)
            if salary_matches:
                parameters['salary_data'] = [
                    {'name': name, 'amount': int(amount)} 
                    for name, amount in salary_matches
                ]
            
            return {
                'is_instruction': True,
                'instruction': 'create_salary_table',
                'parameters': parameters,
                'response': f"正在为您创建工资表: {parameters.get('project_name', '未指定项目')}"
            }
            
        except Exception as e:
            logger.error(f"解析创建工资表指令失败: {e}")
            return {
                'is_instruction': False,
                'instruction': None,
                'parameters': None,
                'response': None
            }
    
    def _parse_export_instruction(self, message: str) -> Dict[str, Any]:
        """解析导出指令"""
        try:
            parameters = {}
            
            # 判断导出类型
            if '员工' in message:
                parameters['export_type'] = 'employees'
                parameters['format'] = 'excel'
            elif '工资' in message:
                parameters['export_type'] = 'salary'
                parameters['format'] = 'excel'
            elif '支出' in message:
                parameters['export_type'] = 'expense'
                parameters['format'] = 'excel'
            else:
                parameters['export_type'] = 'all'
                parameters['format'] = 'excel'
            
            return {
                'is_instruction': True,
                'instruction': 'export_data',
                'parameters': parameters,
                'response': f"正在为您导出{parameters.get('export_type', '数据')}..."
            }
            
        except Exception as e:
            logger.error(f"解析导出指令失败: {e}")
            return {
                'is_instruction': False,
                'instruction': None,
                'parameters': None,
                'response': None
            }
    
    async def _test_api_connection(self) -> bool:
        """测试DeepSeek API连接"""
        try:
            headers = {
                'Authorization': f'Bearer {self.deepseek_config["api_key"]}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'model': self.deepseek_config['model'],
                'messages': [
                    {'role': 'user', 'content': '你好'}
                ],
                'max_tokens': 10
            }
            
            async with self.session.post(
                f"{self.deepseek_config['base_url']}/chat/completions",
                headers=headers,
                json=data
            ) as response:
                if response.status == 200:
                    return True
                else:
                    raise Exception(f"API测试失败，状态码: {response.status}")
                    
        except Exception as e:
            logger.error(f"API连接测试失败: {e}")
            raise
    
    async def _generate_response(self, context: str) -> str:
        """使用DeepSeek API生成响应"""
        try:
            if not self.session:
                raise Exception("API会话未初始化")
            
            headers = {
                'Authorization': f'Bearer {self.deepseek_config["api_key"]}',
                'Content-Type': 'application/json'
            }
            
            # 构建消息
            messages = [
                {'role': 'system', 'content': self.system_prompt},
                {'role': 'user', 'content': context}
            ]
            
            data = {
                'model': self.deepseek_config['model'],
                'messages': messages,
                'max_tokens': self.deepseek_config.get('max_tokens', 2048),
                'temperature': self.deepseek_config.get('temperature', 0.7),
                'stream': False
            }
            
            async with self.session.post(
                f"{self.deepseek_config['base_url']}/chat/completions",
                headers=headers,
                json=data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result['choices'][0]['message']['content'].strip()
                else:
                    error_text = await response.text()
                    logger.error(f"DeepSeek API错误: {response.status} - {error_text}")
                    return "抱歉，AI服务暂时不可用，请稍后再试。"
                    
        except Exception as e:
            logger.error(f"DeepSeek API调用失败: {e}")
            return "抱歉，处理您的请求时出现了错误，请稍后再试。"
    
    def speech_to_text(self, audio_data: bytes) -> Dict[str, Any]:
        """语音转文字"""
        try:
            # 将音频数据转换为AudioData对象
            audio_file = BytesIO(audio_data)
            
            with sr.AudioFile(audio_file) as source:
                audio = self.speech_recognizer.record(source)
            
            # 使用Google语音识别（需要网络）
            try:
                text = self.speech_recognizer.recognize_google(audio, language='zh-CN')
                return {
                    'success': True,
                    'text': text,
                    'confidence': 0.9
                }
            except sr.UnknownValueError:
                return {
                    'success': False,
                    'error': '无法识别语音内容',
                    'text': ''
                }
            except sr.RequestError as e:
                # 如果Google服务不可用，尝试使用离线识别
                return {
                    'success': False,
                    'error': f'语音识别服务错误: {str(e)}',
                    'text': ''
                }
                
        except Exception as e:
            logger.error(f"语音转文字失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'text': ''
            }
    
    def text_to_speech(self, text: str) -> Dict[str, Any]:
        """文字转语音"""
        try:
            if not self.tts_engine:
                return {
                    'success': False,
                    'error': 'TTS引擎未初始化',
                    'audio_data': None
                }
            
            # 创建临时文件来保存音频
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name
            
            # 保存音频到临时文件
            self.tts_engine.save_to_file(text, temp_path)
            self.tts_engine.runAndWait()
            
            # 读取音频数据
            with open(temp_path, 'rb') as f:
                audio_data = f.read()
            
            # 删除临时文件
            os.unlink(temp_path)
            
            return {
                'success': True,
                'audio_data': audio_data,
                'format': 'wav'
            }
            
        except Exception as e:
            logger.error(f"文字转语音失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'audio_data': None
            }
    
    def get_model_status(self) -> Dict[str, Any]:
        """获取模型状态"""
        return {
            'is_loaded': self.is_model_loaded,
            'status': self.model_status,
            'model_info': {
                'name': 'DeepSeek Chat',
                'model': self.deepseek_config.get('model', 'deepseek-chat'),
                'type': 'api',
                'base_url': self.deepseek_config.get('base_url', ''),
                'max_tokens': self.deepseek_config.get('max_tokens', 2048),
                'temperature': self.deepseek_config.get('temperature', 0.7)
            },
            'capabilities': {
                'text_chat': True,
                'voice_recognition': True,
                'text_to_speech': self.tts_engine is not None,
                'instruction_parsing': True,
                'api_based': True
            }
        }
    
    def get_available_instructions(self) -> List[Dict[str, Any]]:
        """获取可用指令列表"""
        return [
            {
                'name': 'add_employee',
                'description': '添加员工信息',
                'examples': [
                    '添加员工张三，身份证110101199001011234，手机13800138000',
                    '新增员工李四，身份证号110101199002022345'
                ],
                'parameters': ['name', 'id_card', 'phone', 'bank_card', 'bank_name']
            },
            {
                'name': 'create_salary_table',
                'description': '创建工资表',
                'examples': [
                    '创建项目A工资表，张三8000元，李四7500元',
                    '生成2024年3月工资表'
                ],
                'parameters': ['project_name', 'period', 'salary_data']
            },
            {
                'name': 'export_data',
                'description': '导出数据',
                'examples': [
                    '导出员工信息',
                    '下载工资表',
                    '生成支出报表'
                ],
                'parameters': ['export_type', 'format']
            },
            {
                'name': 'backup_data',
                'description': '备份数据',
                'examples': [
                    '备份数据',
                    '创建数据备份'
                ],
                'parameters': []
            }
        ]
    
    async def reload_model(self) -> Dict[str, Any]:
        """重新初始化DeepSeek API连接"""
        # 关闭现有会话
        if self.session:
            await self.session.close()
            self.session = None
        
        self.is_model_loaded = False
        self.model_status = 'not_loaded'
        return await self.load_model()
    
    async def close(self):
        """关闭资源"""
        if self.session:
            await self.session.close()
            self.session = None
    
    def __del__(self):
        """析构函数"""
        if self.session and not self.session.closed:
            # 在事件循环中关闭会话
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self.session.close())
                else:
                    loop.run_until_complete(self.session.close())
            except:
                pass

def create_ai_manager() -> AIModelManager:
    """创建AI模型管理器实例"""
    return AIModelManager()

# 全局AI管理器实例
ai_manager = None

def get_ai_manager() -> AIModelManager:
    """获取AI管理器实例"""
    global ai_manager
    if ai_manager is None:
        ai_manager = create_ai_manager()
    return ai_manager