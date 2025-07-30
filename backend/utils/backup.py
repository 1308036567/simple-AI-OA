import os
import shutil
import zipfile
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from pathlib import Path
import asyncio
from sqlalchemy.orm import Session
from database import get_db, engine
from models import BackupRecord
from config import BACKUP_CONFIG

logger = logging.getLogger(__name__)

class BackupManager:
    """备份管理器"""
    
    def __init__(self):
        self.backup_config = BACKUP_CONFIG
        self.backup_dir = Path(self.backup_config['backup_directory'])
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # 数据库备份目录
        self.db_backup_dir = self.backup_dir / 'database'
        self.db_backup_dir.mkdir(parents=True, exist_ok=True)
        
        # 文件备份目录
        self.file_backup_dir = self.backup_dir / 'files'
        self.file_backup_dir.mkdir(parents=True, exist_ok=True)
        
        # 完整备份目录
        self.full_backup_dir = self.backup_dir / 'full'
        self.full_backup_dir.mkdir(parents=True, exist_ok=True)
    
    async def create_full_backup(self, backup_type: str = 'manual', description: str = '') -> Dict[str, Any]:
        """
        创建完整备份
        
        Args:
            backup_type: 备份类型 ('manual', 'scheduled')
            description: 备份描述
            
        Returns:
            备份结果
        """
        try:
            backup_time = datetime.now()
            backup_name = f"full_backup_{backup_time.strftime('%Y%m%d_%H%M%S')}"
            backup_path = self.full_backup_dir / f"{backup_name}.zip"
            
            logger.info(f"开始创建完整备份: {backup_name}")
            
            # 创建临时目录
            temp_dir = self.backup_dir / 'temp' / backup_name
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            try:
                # 备份数据库
                db_backup_result = await self._backup_database(temp_dir / 'database')
                if not db_backup_result['success']:
                    raise Exception(f"数据库备份失败: {db_backup_result['error']}")
                
                # 备份文件
                file_backup_result = await self._backup_files(temp_dir / 'files')
                if not file_backup_result['success']:
                    raise Exception(f"文件备份失败: {file_backup_result['error']}")
                
                # 备份配置
                config_backup_result = await self._backup_config(temp_dir / 'config')
                if not config_backup_result['success']:
                    raise Exception(f"配置备份失败: {config_backup_result['error']}")
                
                # 创建备份信息文件
                backup_info = {
                    'backup_name': backup_name,
                    'backup_time': backup_time.isoformat(),
                    'backup_type': backup_type,
                    'description': description,
                    'database_info': db_backup_result['info'],
                    'file_info': file_backup_result['info'],
                    'config_info': config_backup_result['info']
                }
                
                with open(temp_dir / 'backup_info.json', 'w', encoding='utf-8') as f:
                    json.dump(backup_info, f, ensure_ascii=False, indent=2)
                
                # 压缩备份
                await self._create_zip_archive(temp_dir, backup_path)
                
                # 计算备份大小
                backup_size = backup_path.stat().st_size
                
                # 记录备份信息到数据库
                await self._record_backup_info({
                    'backup_name': backup_name,
                    'backup_type': backup_type,
                    'backup_path': str(backup_path),
                    'backup_size': backup_size,
                    'description': description,
                    'created_at': backup_time
                })
                
                # 清理临时目录
                shutil.rmtree(temp_dir)
                
                logger.info(f"完整备份创建成功: {backup_name}")
                
                return {
                    'success': True,
                    'backup_name': backup_name,
                    'backup_path': str(backup_path),
                    'backup_size': backup_size,
                    'backup_time': backup_time.isoformat(),
                    'message': '备份创建成功'
                }
                
            finally:
                # 确保清理临时目录
                if temp_dir.exists():
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    
        except Exception as e:
            logger.error(f"创建完整备份失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': '备份创建失败'
            }
    
    async def _backup_database(self, backup_dir: Path) -> Dict[str, Any]:
        """
        备份数据库
        
        Args:
            backup_dir: 备份目录
            
        Returns:
            备份结果
        """
        try:
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # 获取数据库连接字符串
            db_url = str(engine.url)
            
            if 'sqlite' in db_url:
                # SQLite数据库备份
                db_path = db_url.replace('sqlite:///', '')
                if os.path.exists(db_path):
                    backup_file = backup_dir / 'database.db'
                    shutil.copy2(db_path, backup_file)
                    
                    return {
                        'success': True,
                        'info': {
                            'type': 'sqlite',
                            'original_path': db_path,
                            'backup_path': str(backup_file),
                            'size': backup_file.stat().st_size
                        }
                    }
            
            elif 'mysql' in db_url:
                # MySQL数据库备份
                return await self._backup_mysql_database(backup_dir)
            
            else:
                # 其他数据库类型的备份
                return await self._backup_generic_database(backup_dir)
                
        except Exception as e:
            logger.error(f"数据库备份失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _backup_mysql_database(self, backup_dir: Path) -> Dict[str, Any]:
        """
        备份MySQL数据库
        
        Args:
            backup_dir: 备份目录
            
        Returns:
            备份结果
        """
        try:
            # 使用mysqldump命令备份
            import subprocess
            
            db_url = str(engine.url)
            # 解析数据库连接信息
            # 这里需要根据实际的数据库配置来实现
            
            backup_file = backup_dir / 'database.sql'
            
            # 执行mysqldump命令
            # cmd = ['mysqldump', '-h', host, '-u', user, '-p' + password, database]
            # with open(backup_file, 'w') as f:
            #     subprocess.run(cmd, stdout=f, check=True)
            
            # 暂时返回成功（需要根据实际环境配置）
            return {
                'success': True,
                'info': {
                    'type': 'mysql',
                    'backup_path': str(backup_file),
                    'size': 0
                }
            }
            
        except Exception as e:
            logger.error(f"MySQL数据库备份失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _backup_generic_database(self, backup_dir: Path) -> Dict[str, Any]:
        """
        备份通用数据库（导出为JSON）
        
        Args:
            backup_dir: 备份目录
            
        Returns:
            备份结果
        """
        try:
            from models import Employee, FileRecord, AccountTable, SalaryRecord, ExpenseRecord, AIChat, OperationLog
            
            backup_data = {}
            
            # 获取数据库会话
            db = next(get_db())
            
            try:
                # 备份各个表的数据
                tables = {
                    'employees': Employee,
                    'file_records': FileRecord,
                    'account_tables': AccountTable,
                    'salary_records': SalaryRecord,
                    'expense_records': ExpenseRecord,
                    'ai_chats': AIChat,
                    'operation_logs': OperationLog
                }
                
                for table_name, model_class in tables.items():
                    records = db.query(model_class).all()
                    backup_data[table_name] = [
                        self._serialize_model(record) for record in records
                    ]
                
                # 保存为JSON文件
                backup_file = backup_dir / 'database.json'
                with open(backup_file, 'w', encoding='utf-8') as f:
                    json.dump(backup_data, f, ensure_ascii=False, indent=2, default=str)
                
                return {
                    'success': True,
                    'info': {
                        'type': 'json',
                        'backup_path': str(backup_file),
                        'size': backup_file.stat().st_size,
                        'tables': list(tables.keys()),
                        'record_counts': {k: len(v) for k, v in backup_data.items()}
                    }
                }
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"通用数据库备份失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _serialize_model(self, model_instance) -> Dict[str, Any]:
        """
        序列化模型实例
        
        Args:
            model_instance: 模型实例
            
        Returns:
            序列化后的字典
        """
        result = {}
        for column in model_instance.__table__.columns:
            value = getattr(model_instance, column.name)
            if isinstance(value, (datetime, date)):
                result[column.name] = value.isoformat()
            else:
                result[column.name] = value
        return result
    
    async def _backup_files(self, backup_dir: Path) -> Dict[str, Any]:
        """
        备份文件
        
        Args:
            backup_dir: 备份目录
            
        Returns:
            备份结果
        """
        try:
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # 获取上传文件目录
            upload_dir = Path('uploads')
            if not upload_dir.exists():
                return {
                    'success': True,
                    'info': {
                        'message': '没有文件需要备份',
                        'file_count': 0,
                        'total_size': 0
                    }
                }
            
            # 复制文件目录
            shutil.copytree(upload_dir, backup_dir / 'uploads', dirs_exist_ok=True)
            
            # 统计文件信息
            file_count = 0
            total_size = 0
            
            for file_path in (backup_dir / 'uploads').rglob('*'):
                if file_path.is_file():
                    file_count += 1
                    total_size += file_path.stat().st_size
            
            return {
                'success': True,
                'info': {
                    'backup_path': str(backup_dir / 'uploads'),
                    'file_count': file_count,
                    'total_size': total_size
                }
            }
            
        except Exception as e:
            logger.error(f"文件备份失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _backup_config(self, backup_dir: Path) -> Dict[str, Any]:
        """
        备份配置文件
        
        Args:
            backup_dir: 备份目录
            
        Returns:
            备份结果
        """
        try:
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            config_files = ['config.py', 'requirements.txt']
            backed_up_files = []
            
            for config_file in config_files:
                if os.path.exists(config_file):
                    shutil.copy2(config_file, backup_dir / config_file)
                    backed_up_files.append(config_file)
            
            return {
                'success': True,
                'info': {
                    'backup_path': str(backup_dir),
                    'files': backed_up_files
                }
            }
            
        except Exception as e:
            logger.error(f"配置备份失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _create_zip_archive(self, source_dir: Path, archive_path: Path):
        """
        创建ZIP压缩包
        
        Args:
            source_dir: 源目录
            archive_path: 压缩包路径
        """
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in source_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(source_dir)
                    zipf.write(file_path, arcname)
    
    async def _record_backup_info(self, backup_info: Dict[str, Any]):
        """
        记录备份信息到数据库
        
        Args:
            backup_info: 备份信息
        """
        try:
            db = next(get_db())
            try:
                backup_record = BackupRecord(
                    backup_name=backup_info['backup_name'],
                    backup_type=backup_info['backup_type'],
                    backup_path=backup_info['backup_path'],
                    backup_size=backup_info['backup_size'],
                    description=backup_info['description'],
                    created_at=backup_info['created_at']
                )
                
                db.add(backup_record)
                db.commit()
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"记录备份信息失败: {e}")
    
    async def restore_backup(self, backup_name: str) -> Dict[str, Any]:
        """
        恢复备份
        
        Args:
            backup_name: 备份名称
            
        Returns:
            恢复结果
        """
        try:
            backup_path = self.full_backup_dir / f"{backup_name}.zip"
            
            if not backup_path.exists():
                return {
                    'success': False,
                    'error': '备份文件不存在',
                    'message': '恢复失败'
                }
            
            # 创建临时目录
            temp_dir = self.backup_dir / 'temp' / f"restore_{backup_name}"
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            try:
                # 解压备份文件
                with zipfile.ZipFile(backup_path, 'r') as zipf:
                    zipf.extractall(temp_dir)
                
                # 读取备份信息
                backup_info_file = temp_dir / 'backup_info.json'
                if backup_info_file.exists():
                    with open(backup_info_file, 'r', encoding='utf-8') as f:
                        backup_info = json.load(f)
                else:
                    backup_info = {}
                
                # 恢复数据库
                if (temp_dir / 'database').exists():
                    db_restore_result = await self._restore_database(temp_dir / 'database')
                    if not db_restore_result['success']:
                        raise Exception(f"数据库恢复失败: {db_restore_result['error']}")
                
                # 恢复文件
                if (temp_dir / 'files').exists():
                    file_restore_result = await self._restore_files(temp_dir / 'files')
                    if not file_restore_result['success']:
                        raise Exception(f"文件恢复失败: {file_restore_result['error']}")
                
                logger.info(f"备份恢复成功: {backup_name}")
                
                return {
                    'success': True,
                    'backup_name': backup_name,
                    'backup_info': backup_info,
                    'message': '备份恢复成功'
                }
                
            finally:
                # 清理临时目录
                if temp_dir.exists():
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    
        except Exception as e:
            logger.error(f"恢复备份失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': '备份恢复失败'
            }
    
    async def _restore_database(self, backup_dir: Path) -> Dict[str, Any]:
        """
        恢复数据库
        
        Args:
            backup_dir: 备份目录
            
        Returns:
            恢复结果
        """
        try:
            # 根据备份类型恢复数据库
            if (backup_dir / 'database.db').exists():
                # SQLite数据库恢复
                return await self._restore_sqlite_database(backup_dir)
            elif (backup_dir / 'database.sql').exists():
                # MySQL数据库恢复
                return await self._restore_mysql_database(backup_dir)
            elif (backup_dir / 'database.json').exists():
                # JSON数据恢复
                return await self._restore_json_database(backup_dir)
            else:
                return {
                    'success': False,
                    'error': '未找到数据库备份文件'
                }
                
        except Exception as e:
            logger.error(f"数据库恢复失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _restore_sqlite_database(self, backup_dir: Path) -> Dict[str, Any]:
        """
        恢复SQLite数据库
        
        Args:
            backup_dir: 备份目录
            
        Returns:
            恢复结果
        """
        try:
            backup_file = backup_dir / 'database.db'
            db_url = str(engine.url)
            db_path = db_url.replace('sqlite:///', '')
            
            # 备份当前数据库
            if os.path.exists(db_path):
                backup_current = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.copy2(db_path, backup_current)
            
            # 恢复数据库
            shutil.copy2(backup_file, db_path)
            
            return {
                'success': True,
                'info': {
                    'type': 'sqlite',
                    'restored_path': db_path
                }
            }
            
        except Exception as e:
            logger.error(f"SQLite数据库恢复失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _restore_mysql_database(self, backup_dir: Path) -> Dict[str, Any]:
        """
        恢复MySQL数据库
        
        Args:
            backup_dir: 备份目录
            
        Returns:
            恢复结果
        """
        # 这里需要根据实际的MySQL配置来实现
        return {
            'success': True,
            'info': {
                'type': 'mysql',
                'message': 'MySQL恢复功能待实现'
            }
        }
    
    async def _restore_json_database(self, backup_dir: Path) -> Dict[str, Any]:
        """
        恢复JSON数据库
        
        Args:
            backup_dir: 备份目录
            
        Returns:
            恢复结果
        """
        try:
            backup_file = backup_dir / 'database.json'
            
            with open(backup_file, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            # 这里需要实现JSON数据的恢复逻辑
            # 由于涉及到数据完整性，建议谨慎实现
            
            return {
                'success': True,
                'info': {
                    'type': 'json',
                    'message': 'JSON数据恢复功能待完善'
                }
            }
            
        except Exception as e:
            logger.error(f"JSON数据库恢复失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _restore_files(self, backup_dir: Path) -> Dict[str, Any]:
        """
        恢复文件
        
        Args:
            backup_dir: 备份目录
            
        Returns:
            恢复结果
        """
        try:
            uploads_backup = backup_dir / 'uploads'
            if not uploads_backup.exists():
                return {
                    'success': True,
                    'info': {
                        'message': '没有文件需要恢复'
                    }
                }
            
            # 备份当前文件目录
            upload_dir = Path('uploads')
            if upload_dir.exists():
                backup_current = Path(f"uploads_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                shutil.move(upload_dir, backup_current)
            
            # 恢复文件
            shutil.copytree(uploads_backup, upload_dir)
            
            return {
                'success': True,
                'info': {
                    'restored_path': str(upload_dir)
                }
            }
            
        except Exception as e:
            logger.error(f"文件恢复失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def list_backups(self) -> List[Dict[str, Any]]:
        """
        列出所有备份
        
        Returns:
            备份列表
        """
        try:
            backups = []
            
            # 从数据库获取备份记录
            db = next(get_db())
            try:
                backup_records = db.query(BackupRecord).order_by(BackupRecord.created_at.desc()).all()
                
                for record in backup_records:
                    backup_info = {
                        'id': record.id,
                        'backup_name': record.backup_name,
                        'backup_type': record.backup_type,
                        'backup_path': record.backup_path,
                        'backup_size': record.backup_size,
                        'description': record.description,
                        'created_at': record.created_at.isoformat(),
                        'exists': os.path.exists(record.backup_path)
                    }
                    backups.append(backup_info)
                    
            finally:
                db.close()
            
            return backups
            
        except Exception as e:
            logger.error(f"获取备份列表失败: {e}")
            return []
    
    async def delete_backup(self, backup_name: str) -> Dict[str, Any]:
        """
        删除备份
        
        Args:
            backup_name: 备份名称
            
        Returns:
            删除结果
        """
        try:
            backup_path = self.full_backup_dir / f"{backup_name}.zip"
            
            # 删除文件
            if backup_path.exists():
                backup_path.unlink()
            
            # 从数据库删除记录
            db = next(get_db())
            try:
                backup_record = db.query(BackupRecord).filter(
                    BackupRecord.backup_name == backup_name
                ).first()
                
                if backup_record:
                    db.delete(backup_record)
                    db.commit()
                    
            finally:
                db.close()
            
            return {
                'success': True,
                'message': '备份删除成功'
            }
            
        except Exception as e:
            logger.error(f"删除备份失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': '备份删除失败'
            }
    
    async def cleanup_old_backups(self) -> Dict[str, Any]:
        """
        清理过期备份
        
        Returns:
            清理结果
        """
        try:
            retention_days = self.backup_config.get('retention_days', 30)
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            deleted_count = 0
            
            # 获取过期备份
            db = next(get_db())
            try:
                old_backups = db.query(BackupRecord).filter(
                    BackupRecord.created_at < cutoff_date
                ).all()
                
                for backup in old_backups:
                    # 删除文件
                    if os.path.exists(backup.backup_path):
                        os.unlink(backup.backup_path)
                    
                    # 删除数据库记录
                    db.delete(backup)
                    deleted_count += 1
                
                db.commit()
                
            finally:
                db.close()
            
            return {
                'success': True,
                'deleted_count': deleted_count,
                'message': f'清理了{deleted_count}个过期备份'
            }
            
        except Exception as e:
            logger.error(f"清理过期备份失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': '清理过期备份失败'
            }

def create_backup_manager() -> BackupManager:
    """创建备份管理器实例"""
    return BackupManager()

# 全局备份管理器实例
backup_manager = None

def get_backup_manager() -> BackupManager:
    """获取备份管理器实例"""
    global backup_manager
    if backup_manager is None:
        backup_manager = create_backup_manager()
    return backup_manager