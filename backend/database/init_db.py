import sqlite3
import os

def init_database():
    """初始化数据库，创建所有表"""
    # 确保数据库目录存在
    db_dir = os.path.dirname(os.path.abspath(__file__))
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
    
    db_path = os.path.join(db_dir, 'company.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 创建项目表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            project_id TEXT PRIMARY KEY NOT NULL,
            project_name TEXT NOT NULL,
            project_manager TEXT NOT NULL,
            start_date DATE,
            end_date DATE,
            FOREIGN KEY (project_manager) REFERENCES employees(employee_id)
        )
    ''')
    
    # 创建员工表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            employee_id TEXT PRIMARY KEY NOT NULL,
            name TEXT NOT NULL,
            id_card TEXT UNIQUE NOT NULL,
            phone TEXT UNIQUE NOT NULL,
            bank_card TEXT UNIQUE NOT NULL,
            bank_name TEXT NOT NULL,
            position TEXT NOT NULL,
            department TEXT NOT NULL,
            status TEXT NOT NULL CHECK (status IN ('在职', '离职', '休假'))
        )
    ''')
    
    # 创建文件表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS files (
            file_id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id TEXT NOT NULL,
            file_name TEXT NOT NULL,
            file_path TEXT UNIQUE NOT NULL,
            upload_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(project_id)
        )
    ''')
    
    # 创建工人工资表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS salaries (
            salary_id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT NOT NULL,
            project_id TEXT NOT NULL,
            amount DECIMAL(10,2) NOT NULL,
            work_hours DECIMAL(8,2),
            payment_status TEXT NOT NULL CHECK (payment_status IN ('已发', '未发')),
            salary_date DATE DEFAULT CURRENT_DATE,
            FOREIGN KEY (employee_id) REFERENCES employees(employee_id),
            FOREIGN KEY (project_id) REFERENCES projects(project_id),
            UNIQUE(employee_id, project_id)
        )
    ''')
    
    # 创建项目开销表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            expense_id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id TEXT NOT NULL,
            unit TEXT NOT NULL,
            quantity DECIMAL(10,2) NOT NULL,
            amount DECIMAL(10,2) NOT NULL,
            expense_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            expense_type TEXT NOT NULL CHECK (expense_type IN ('材料采购', '设备租赁', '人工支出')),
            FOREIGN KEY (project_id) REFERENCES projects(project_id),
            UNIQUE(project_id, expense_time, expense_type)
        )
    ''')
    
    # 插入一些示例数据
    # 示例员工数据
    cursor.execute('''
        INSERT OR IGNORE INTO employees 
        (employee_id, name, id_card, phone, bank_card, bank_name, position, department, status)
        VALUES 
        ('EMP001', '张三', '110101199001011234', '13800138001', '6222021234567890', '中国银行', '项目经理', '技术部', '在职'),
        ('EMP002', '李四', '110101199002021235', '13800138002', '6222021234567891', '工商银行', '技术员', '技术部', '在职'),
        ('EMP003', '王五', '110101199003031236', '13800138003', '6222021234567892', '建设银行', '财务', '财务部', '在职')
    ''')
    
    # 示例项目数据
    cursor.execute('''
        INSERT OR IGNORE INTO projects 
        (project_id, project_name, project_manager, start_date, end_date)
        VALUES 
        ('PRJ001', '办公楼装修项目', 'EMP001', '2024-01-01', '2024-06-30'),
        ('PRJ002', '厂房建设项目', 'EMP001', '2024-03-01', '2024-12-31')
    ''')
    
    # 示例工资数据
    cursor.execute('''
        INSERT OR IGNORE INTO salaries 
        (employee_id, project_id, amount, work_hours, payment_status, salary_date)
        VALUES 
        ('EMP001', 'PRJ001', 8000.00, 160.0, '已发', '2024-01-31'),
        ('EMP002', 'PRJ001', 6000.00, 160.0, '已发', '2024-01-31'),
        ('EMP003', 'PRJ001', 5000.00, 160.0, '未发', '2024-01-31'),
        ('EMP001', 'PRJ002', 8500.00, 170.0, '已发', '2024-03-31'),
        ('EMP002', 'PRJ002', 6200.00, 165.0, '未发', '2024-03-31')
    ''')
    
    # 示例开销数据
    cursor.execute('''
        INSERT OR IGNORE INTO expenses 
        (project_id, unit, quantity, amount, expense_time, expense_type)
        VALUES 
        ('PRJ001', '平方米', 100.0, 15000.00, '2024-01-15 10:00:00', '材料采购'),
        ('PRJ001', '台', 2.0, 3000.00, '2024-01-20 14:30:00', '设备租赁'),
        ('PRJ002', '吨', 50.0, 25000.00, '2024-03-10 09:00:00', '材料采购'),
        ('PRJ002', '人天', 30.0, 12000.00, '2024-03-15 16:00:00', '人工支出')
    ''')
    
    conn.commit()
    conn.close()
    print(f"数据库初始化完成，数据库文件位置: {db_path}")

if __name__ == '__main__':
    init_database()