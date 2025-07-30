from pydantic import BaseModel, validator
from typing import Optional, Dict, Any, List
from datetime import datetime

class ChatRequest(BaseModel):
    """聊天请求模型"""
    message: str
    session_id: Optional[str] = None
    
    @validator('message')
    def validate_message(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('消息内容不能为空')
        if len(v) > 2000:
            raise ValueError('消息内容长度不能超过2000个字符')
        return v.strip()

class ChatResponse(BaseModel):
    """聊天响应模型"""
    session_id: str
    message: str
    command_type: Optional[str] = None
    execution_result: Optional[Dict[str, Any]] = None
    timestamp: datetime

class VoiceRequest(BaseModel):
    """语音请求模型"""
    session_id: Optional[str] = None
    audio_format: str = 'wav'
    
    @validator('audio_format')
    def validate_audio_format(cls, v):
        valid_formats = ['wav', 'mp3', 'm4a', 'flac']
        if v not in valid_formats:
            raise ValueError(f'不支持的音频格式，支持的格式：{", ".join(valid_formats)}')
        return v

class VoiceResponse(BaseModel):
    """语音响应模型"""
    recognized_text: str
    chat_response: ChatResponse

class ChatHistoryItem(BaseModel):
    """聊天历史项模型"""
    id: int
    user_input: str
    user_input_type: str
    ai_response: str
    command_type: Optional[str]
    execution_result: Optional[Dict[str, Any]]
    created_at: datetime
    
    class Config:
        from_attributes = True

class ChatHistoryResponse(BaseModel):
    """聊天历史响应模型"""
    session_id: str
    history: List[ChatHistoryItem]
    total: int
    skip: int
    limit: int

class CommandInfo(BaseModel):
    """指令信息模型"""
    name: str
    pattern: str
    example: str
    description: Optional[str] = None

class AvailableCommandsResponse(BaseModel):
    """可用指令响应模型"""
    commands: List[CommandInfo]
    total: int

class ModelStatus(BaseModel):
    """模型状态模型"""
    name: str
    status: str  # 'loaded', 'loading', 'error', 'not_loaded'
    model_path: str
    load_time: Optional[datetime] = None
    error_message: Optional[str] = None
    memory_usage: Optional[float] = None  # MB

class AIModelStatusResponse(BaseModel):
    """AI模型状态响应模型"""
    ai_model: ModelStatus
    voice_recognizer: ModelStatus
    timestamp: datetime

class CommandParseResult(BaseModel):
    """指令解析结果模型"""
    type: str  # 'command', 'question', 'chat'
    action: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    confidence: float = 0.0
    original_text: str

class ExecutionResult(BaseModel):
    """指令执行结果模型"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None
    execution_time: Optional[float] = None  # 秒

class SessionInfo(BaseModel):
    """会话信息模型"""
    session_id: str
    created_at: datetime
    last_activity: datetime
    message_count: int
    status: str  # 'active', 'inactive', 'expired'

class SessionListResponse(BaseModel):
    """会话列表响应模型"""
    sessions: List[SessionInfo]
    total: int
    active_count: int

class AICapabilities(BaseModel):
    """AI能力模型"""
    text_generation: bool
    voice_recognition: bool
    command_parsing: bool
    data_analysis: bool
    file_processing: bool
    chart_generation: bool

class SystemPrompt(BaseModel):
    """系统提示词模型"""
    role: str
    content: str
    priority: int = 0

class AIConfigRequest(BaseModel):
    """AI配置请求模型"""
    model_name: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    system_prompts: Optional[List[SystemPrompt]] = None
    
    @validator('temperature')
    def validate_temperature(cls, v):
        if v is not None and (v < 0 or v > 2):
            raise ValueError('temperature必须在0-2之间')
        return v
    
    @validator('max_tokens')
    def validate_max_tokens(cls, v):
        if v is not None and (v < 1 or v > 4096):
            raise ValueError('max_tokens必须在1-4096之间')
        return v

class AIConfigResponse(BaseModel):
    """AI配置响应模型"""
    model_name: str
    max_tokens: int
    temperature: float
    system_prompts: List[SystemPrompt]
    capabilities: AICapabilities
    last_updated: datetime

class VoiceSettings(BaseModel):
    """语音设置模型"""
    language: str = 'zh-cn'
    sample_rate: int = 16000
    channels: int = 1
    enable_vad: bool = True  # 语音活动检测
    noise_reduction: bool = True
    
    @validator('sample_rate')
    def validate_sample_rate(cls, v):
        valid_rates = [8000, 16000, 22050, 44100, 48000]
        if v not in valid_rates:
            raise ValueError(f'不支持的采样率，支持的采样率：{valid_rates}')
        return v
    
    @validator('channels')
    def validate_channels(cls, v):
        if v not in [1, 2]:
            raise ValueError('声道数只支持1（单声道）或2（立体声）')
        return v

class VoiceSettingsResponse(BaseModel):
    """语音设置响应模型"""
    settings: VoiceSettings
    supported_languages: List[str]
    model_info: Dict[str, Any]