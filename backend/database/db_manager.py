import sqlite3
import os
from datetime import datetime

class DatabaseManager:
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(__file__), 'company.db')
    
    def get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 使查询结果可以像字典一样访问
        return conn
    
    def execute_query(self, query, params=None):
        """执行查询语句"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            result = cursor.fetchall()
            return [dict(row) for row in result]
        finally:
            conn.close()
    
    def execute_update(self, query, params=None):
        """执行更新语句（INSERT, UPDATE, DELETE）"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()
    
    # 员工相关操作
    def get_all_employees(self):
        """获取所有员工信息"""
        query = "SELECT * FROM employees ORDER BY employee_id"
        return self.execute_query(query)
    
    def get_employee_by_id(self, employee_id):
        """根据员工ID获取员工信息"""
        query = "SELECT * FROM employees WHERE employee_id = ?"
        result = self.execute_query(query, (employee_id,))
        return result[0] if result else None
    
    def search_employees(self, keyword):
        """搜索员工（按姓名或员工编号）"""
        query = "SELECT * FROM employees WHERE name LIKE ? OR employee_id LIKE ?"
        keyword = f"%{keyword}%"
        return self.execute_query(query, (keyword, keyword))
    
    def add_employee(self, employee_data):
        """添加员工"""
        query = '''
            INSERT INTO employees 
            (employee_id, name, id_card, phone, bank_card, bank_name, position, department, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        params = (
            employee_data['employee_id'],
            employee_data['name'],
            employee_data['id_card'],
            employee_data['phone'],
            employee_data['bank_card'],
            employee_data['bank_name'],
            employee_data['position'],
            employee_data['department'],
            employee_data['status']
        )
        return self.execute_update(query, params)
    
    def update_employee(self, employee_id, employee_data):
        """更新员工信息"""
        query = '''
            UPDATE employees 
            SET name=?, id_card=?, phone=?, bank_card=?, bank_name=?, position=?, department=?, status=?
            WHERE employee_id=?
        '''
        params = (
            employee_data['name'],
            employee_data['id_card'],
            employee_data['phone'],
            employee_data['bank_card'],
            employee_data['bank_name'],
            employee_data['position'],
            employee_data['department'],
            employee_data['status'],
            employee_id
        )
        return self.execute_update(query, params)
    
    def delete_employee(self, employee_id):
        """删除员工"""
        query = "DELETE FROM employees WHERE employee_id = ?"
        return self.execute_update(query, (employee_id,))
    
    # 项目相关操作
    def get_all_projects(self):
        """获取所有项目信息"""
        query = "SELECT * FROM projects ORDER BY project_id"
        return self.execute_query(query)
    
    def get_project_by_id(self, project_id):
        """根据项目ID获取项目信息"""
        query = "SELECT * FROM projects WHERE project_id = ?"
        result = self.execute_query(query, (project_id,))
        return result[0] if result else None
    
    # 文件相关操作
    def get_files_by_project(self, project_id=None):
        """获取文件信息（可按项目筛选）"""
        if project_id:
            query = '''
                SELECT f.*, p.project_name 
                FROM files f 
                JOIN projects p ON f.project_id = p.project_id 
                WHERE f.project_id = ?
                ORDER BY f.upload_time DESC
            '''
            return self.execute_query(query, (project_id,))
        else:
            query = '''
                SELECT f.*, p.project_name 
                FROM files f 
                JOIN projects p ON f.project_id = p.project_id 
                ORDER BY f.upload_time DESC
            '''
            return self.execute_query(query)
    
    def add_file(self, file_data):
        """添加文件记录"""
        query = '''
            INSERT INTO files (project_id, file_name, file_path)
            VALUES (?, ?, ?)
        '''
        params = (
            file_data['project_id'],
            file_data['file_name'],
            file_data['file_path']
        )
        return self.execute_update(query, params)
    
    # 工资相关操作
    def get_salaries(self, month=None):
        """获取工资记录（可按月份筛选）"""
        if month:
            query = '''
                SELECT s.*, e.name as employee_name, p.project_name 
                FROM salaries s 
                JOIN employees e ON s.employee_id = e.employee_id 
                JOIN projects p ON s.project_id = p.project_id 
                WHERE strftime('%Y-%m', s.salary_date) = ?
                ORDER BY s.salary_date DESC
            '''
            return self.execute_query(query, (month,))
        else:
            query = '''
                SELECT s.*, e.name as employee_name, p.project_name 
                FROM salaries s 
                JOIN employees e ON s.employee_id = e.employee_id 
                JOIN projects p ON s.project_id = p.project_id 
                ORDER BY s.salary_date DESC
            '''
            return self.execute_query(query)
    
    # 开销相关操作
    def get_expenses(self, month=None):
        """获取开销记录（可按月份筛选）"""
        if month:
            query = '''
                SELECT e.*, p.project_name 
                FROM expenses e 
                JOIN projects p ON e.project_id = p.project_id 
                WHERE strftime('%Y-%m', e.expense_time) = ?
                ORDER BY e.expense_time DESC
            '''
            return self.execute_query(query, (month,))
        else:
            query = '''
                SELECT e.*, p.project_name 
                FROM expenses e 
                JOIN projects p ON e.project_id = p.project_id 
                ORDER BY e.expense_time DESC
            '''
            return self.execute_query(query)
    
    # 统计数据
    def get_dashboard_stats(self):
        """获取仪表盘统计数据"""
        stats = {}
        
        # 员工统计
        result = self.execute_query("SELECT COUNT(*) as total FROM employees")
        stats['total_employees'] = result[0]['total']
        
        result = self.execute_query("SELECT COUNT(*) as active FROM employees WHERE status = '在职'")
        stats['active_employees'] = result[0]['active']
        
        # 文件统计
        result = self.execute_query("SELECT COUNT(*) as total FROM files")
        stats['total_files'] = result[0]['total']
        
        # 项目文件统计
        result = self.execute_query('''
            SELECT p.project_name, COUNT(f.file_id) as file_count 
            FROM projects p 
            LEFT JOIN files f ON p.project_id = f.project_id 
            GROUP BY p.project_id, p.project_name
        ''')
        stats['project_files'] = result
        
        # 财务统计
        result = self.execute_query("SELECT SUM(amount) as total FROM salaries")
        stats['monthly_salary'] = result[0]['total'] or 0
        
        result = self.execute_query("SELECT SUM(amount) as total FROM expenses")
        stats['monthly_expenses'] = result[0]['total'] or 0
        
        return stats