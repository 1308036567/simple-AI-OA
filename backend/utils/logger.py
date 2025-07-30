import logging
import logging.handlers
import os
from datetime import datetime
from typing import Optional, Dict, Any
import json
from pathlib import Path
from sqlalchemy.orm import Session
from models import OperationLog

class CustomFormatter(logging.Formatter):
    """自定义日志格式化器"""
    
    def __init__(self):
        super().__init__()
        self.FORMATS = {
            logging.DEBUG: "\033[36m%(asctime)s - %(name)s - %(levelname)s - %(message)s\033[0m",
            logging.INFO: "\033[32m%(asctime)s - %(name)s - %(levelname)s - %(message)s\033[0m",
            logging.WARNING: "\033[33m%(asctime)s - %(name)s - %(levelname)s - %(message)s\033[0m",
            logging.ERROR: "\033[31m%(asctime)s - %(name)s - %(levelname)s - %(message)s\033[0m",
            logging.CRITICAL: "\033[35m%(asctime)s - %(name)s - %(levelname)s - %(message)s\033[0m"
        }
    
    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno, self.FORMATS[logging.INFO])
        formatter = logging.Formatter(log_fmt, datefmt='%Y-%m-%d %H:%M:%S')
        return formatter.format(record)

class DatabaseLogHandler(logging.Handler):
    """数据库日志处理器"""
    
    def __init__(self, db_session_factory):
        super().__init__()
        self.db_session_factory = db_session_factory
        self.setLevel(logging.INFO)
    
    def emit(self, record):
        """发送日志记录到数据库"""
        try:
            # 只记录特定的操作日志
            if hasattr(record, 'operation_type'):
                db = self.db_session_factory()
                try:
                    log_entry = OperationLog(
                        operation_type=getattr(record, 'operation_type', 'unknown'),
                        operation_detail=record.getMessage(),
                        operator=getattr(record, 'operator', 'system'),
                        ip_address=getattr(record, 'ip_address', '127.0.0.1'),
                        user_agent=getattr(record, 'user_agent', ''),
                        request_data=getattr(record, 'request_data', ''),
                        response_data=getattr(record, 'response_data', ''),
                        execution_time=getattr(record, 'execution_time', 0),
                        status=getattr(record, 'status', 'success')
                    )
                    db.add(log_entry)
                    db.commit()
                finally:
                    db.close()
        except Exception as e:
            # 避免日志记录失败影响主程序
            print(f"数据库日志记录失败: {e}")

class LoggerManager:
    """日志管理器"""
    
    def __init__(self, log_dir: str = "logs", db_session_factory=None):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.db_session_factory = db_session_factory
        self.loggers = {}
        
        # 创建主日志记录器
        self.setup_main_logger()
    
    def setup_main_logger(self):
        """设置主日志记录器"""
        logger = logging.getLogger('main')
        logger.setLevel(logging.DEBUG)
        
        # 清除现有处理器
        logger.handlers.clear()
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(CustomFormatter())
        logger.addHandler(console_handler)
        
        # 文件处理器 - 所有日志
        file_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / 'app.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        # 错误日志文件处理器
        error_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / 'error.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        logger.addHandler(error_handler)
        
        # 数据库处理器（如果提供了数据库会话工厂）
        if self.db_session_factory:
            db_handler = DatabaseLogHandler(self.db_session_factory)
            logger.addHandler(db_handler)
        
        self.loggers['main'] = logger
    
    def get_logger(self, name: str) -> logging.Logger:
        """获取指定名称的日志记录器"""
        if name not in self.loggers:
            logger = logging.getLogger(name)
            logger.setLevel(logging.DEBUG)
            
            # 继承主日志记录器的处理器
            main_logger = self.loggers.get('main')
            if main_logger:
                for handler in main_logger.handlers:
                    logger.addHandler(handler)
            
            self.loggers[name] = logger
        
        return self.loggers[name]
    
    def log_operation(self, 
                     operation_type: str,
                     operation_detail: str,
                     operator: str = 'system',
                     ip_address: str = '127.0.0.1',
                     user_agent: str = '',
                     request_data: str = '',
                     response_data: str = '',
                     execution_time: float = 0,
                     status: str = 'success',
                     level: int = logging.INFO):
        """记录操作日志"""
        logger = self.get_logger('operation')
        
        # 创建日志记录
        record = logger.makeRecord(
            logger.name, level, '', 0, operation_detail, (), None
        )
        
        # 添加自定义属性
        record.operation_type = operation_type
        record.operator = operator
        record.ip_address = ip_address
        record.user_agent = user_agent
        record.request_data = request_data
        record.response_data = response_data
        record.execution_time = execution_time
        record.status = status
        
        logger.handle(record)
    
    def log_api_request(self,
                       method: str,
                       url: str,
                       status_code: int,
                       execution_time: float,
                       ip_address: str = '127.0.0.1',
                       user_agent: str = '',
                       request_data: str = '',
                       response_data: str = ''):
        """记录API请求日志"""
        operation_detail = f"{method} {url} - {status_code} ({execution_time:.3f}s)"
        status = 'success' if 200 <= status_code < 400 else 'error'
        level = logging.INFO if status == 'success' else logging.ERROR
        
        self.log_operation(
            operation_type='api_request',
            operation_detail=operation_detail,
            operator='api_user',
            ip_address=ip_address,
            user_agent=user_agent,
            request_data=request_data,
            response_data=response_data,
            execution_time=execution_time,
            status=status,
            level=level
        )
    
    def log_database_operation(self,
                              operation: str,
                              table: str,
                              record_id: Optional[int] = None,
                              operator: str = 'system',
                              details: str = ''):
        """记录数据库操作日志"""
        operation_detail = f"{operation} {table}"
        if record_id:
            operation_detail += f" (ID: {record_id})"
        if details:
            operation_detail += f" - {details}"
        
        self.log_operation(
            operation_type='database',
            operation_detail=operation_detail,
            operator=operator
        )
    
    def log_file_operation(self,
                          operation: str,
                          file_path: str,
                          operator: str = 'system',
                          file_size: Optional[int] = None):
        """记录文件操作日志"""
        operation_detail = f"{operation} {file_path}"
        if file_size:
            operation_detail += f" ({file_size} bytes)"
        
        self.log_operation(
            operation_type='file',
            operation_detail=operation_detail,
            operator=operator
        )
    
    def log_ai_interaction(self,
                          interaction_type: str,
                          user_input: str,
                          ai_response: str,
                          execution_time: float,
                          operator: str = 'user'):
        """记录AI交互日志"""
        operation_detail = f"AI {interaction_type} - {len(user_input)} chars input, {len(ai_response)} chars output"
        
        # 截断过长的数据
        request_data = user_input[:1000] + '...' if len(user_input) > 1000 else user_input
        response_data = ai_response[:1000] + '...' if len(ai_response) > 1000 else ai_response
        
        self.log_operation(
            operation_type='ai_interaction',
            operation_detail=operation_detail,
            operator=operator,
            request_data=request_data,
            response_data=response_data,
            execution_time=execution_time
        )
    
    def log_backup_operation(self,
                           operation: str,
                           backup_path: str,
                           status: str = 'success',
                           details: str = ''):
        """记录备份操作日志"""
        operation_detail = f"Backup {operation}: {backup_path}"
        if details:
            operation_detail += f" - {details}"
        
        level = logging.INFO if status == 'success' else logging.ERROR
        
        self.log_operation(
            operation_type='backup',
            operation_detail=operation_detail,
            operator='system',
            status=status,
            level=level
        )
    
    def log_security_event(self,
                          event_type: str,
                          details: str,
                          ip_address: str = '127.0.0.1',
                          user_agent: str = '',
                          severity: str = 'medium'):
        """记录安全事件日志"""
        operation_detail = f"Security Event [{severity.upper()}]: {event_type} - {details}"
        
        level_map = {
            'low': logging.INFO,
            'medium': logging.WARNING,
            'high': logging.ERROR,
            'critical': logging.CRITICAL
        }
        level = level_map.get(severity, logging.WARNING)
        
        self.log_operation(
            operation_type='security',
            operation_detail=operation_detail,
            operator='security_monitor',
            ip_address=ip_address,
            user_agent=user_agent,
            status='alert',
            level=level
        )
    
    def get_log_stats(self, days: int = 7) -> Dict[str, Any]:
        """获取日志统计信息"""
        try:
            if not self.db_session_factory:
                return {'error': '数据库连接不可用'}
            
            db = self.db_session_factory()
            try:
                from datetime import timedelta
                start_date = datetime.now() - timedelta(days=days)
                
                # 查询指定天数内的日志
                logs = db.query(OperationLog).filter(
                    OperationLog.created_at >= start_date
                ).all()
                
                # 统计分析
                stats = {
                    'total_logs': len(logs),
                    'by_type': {},
                    'by_status': {},
                    'by_operator': {},
                    'error_count': 0,
                    'avg_execution_time': 0
                }
                
                total_execution_time = 0
                execution_count = 0
                
                for log in logs:
                    # 按类型统计
                    op_type = log.operation_type
                    stats['by_type'][op_type] = stats['by_type'].get(op_type, 0) + 1
                    
                    # 按状态统计
                    status = log.status
                    stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
                    
                    # 按操作者统计
                    operator = log.operator
                    stats['by_operator'][operator] = stats['by_operator'].get(operator, 0) + 1
                    
                    # 错误统计
                    if status == 'error':
                        stats['error_count'] += 1
                    
                    # 执行时间统计
                    if log.execution_time > 0:
                        total_execution_time += log.execution_time
                        execution_count += 1
                
                # 计算平均执行时间
                if execution_count > 0:
                    stats['avg_execution_time'] = total_execution_time / execution_count
                
                return stats
                
            finally:
                db.close()
                
        except Exception as e:
            logger = self.get_logger('stats')
            logger.error(f"获取日志统计失败: {e}")
            return {'error': str(e)}
    
    def cleanup_old_logs(self, days: int = 30):
        """清理旧日志"""
        try:
            if not self.db_session_factory:
                return
            
            db = self.db_session_factory()
            try:
                from datetime import timedelta
                cutoff_date = datetime.now() - timedelta(days=days)
                
                # 删除旧的数据库日志
                deleted_count = db.query(OperationLog).filter(
                    OperationLog.created_at < cutoff_date
                ).delete()
                
                db.commit()
                
                logger = self.get_logger('cleanup')
                logger.info(f"清理了 {deleted_count} 条旧日志记录")
                
            finally:
                db.close()
                
        except Exception as e:
            logger = self.get_logger('cleanup')
            logger.error(f"清理旧日志失败: {e}")
    
    def export_logs(self, 
                   start_date: Optional[datetime] = None,
                   end_date: Optional[datetime] = None,
                   operation_types: Optional[list] = None,
                   export_format: str = 'json') -> str:
        """导出日志"""
        try:
            if not self.db_session_factory:
                return ''
            
            db = self.db_session_factory()
            try:
                query = db.query(OperationLog)
                
                # 时间范围过滤
                if start_date:
                    query = query.filter(OperationLog.created_at >= start_date)
                if end_date:
                    query = query.filter(OperationLog.created_at <= end_date)
                
                # 操作类型过滤
                if operation_types:
                    query = query.filter(OperationLog.operation_type.in_(operation_types))
                
                logs = query.order_by(OperationLog.created_at.desc()).all()
                
                if export_format == 'json':
                    log_data = []
                    for log in logs:
                        log_data.append({
                            'id': log.id,
                            'operation_type': log.operation_type,
                            'operation_detail': log.operation_detail,
                            'operator': log.operator,
                            'ip_address': log.ip_address,
                            'user_agent': log.user_agent,
                            'execution_time': log.execution_time,
                            'status': log.status,
                            'created_at': log.created_at.isoformat()
                        })
                    return json.dumps(log_data, ensure_ascii=False, indent=2)
                
                elif export_format == 'csv':
                    import csv
                    import io
                    
                    output = io.StringIO()
                    writer = csv.writer(output)
                    
                    # 写入标题行
                    writer.writerow([
                        'ID', '操作类型', '操作详情', '操作者', 'IP地址', 
                        '用户代理', '执行时间', '状态', '创建时间'
                    ])
                    
                    # 写入数据行
                    for log in logs:
                        writer.writerow([
                            log.id, log.operation_type, log.operation_detail,
                            log.operator, log.ip_address, log.user_agent,
                            log.execution_time, log.status, log.created_at
                        ])
                    
                    return output.getvalue()
                
                return ''
                
            finally:
                db.close()
                
        except Exception as e:
            logger = self.get_logger('export')
            logger.error(f"导出日志失败: {e}")
            return ''

# 全局日志管理器实例
logger_manager = None

def init_logger_manager(log_dir: str = "logs", db_session_factory=None) -> LoggerManager:
    """初始化日志管理器"""
    global logger_manager
    logger_manager = LoggerManager(log_dir, db_session_factory)
    return logger_manager

def get_logger_manager() -> LoggerManager:
    """获取日志管理器实例"""
    global logger_manager
    if logger_manager is None:
        logger_manager = LoggerManager()
    return logger_manager

def get_logger(name: str = 'main') -> logging.Logger:
    """获取日志记录器"""
    return get_logger_manager().get_logger(name)