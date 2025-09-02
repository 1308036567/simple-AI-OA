from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
from datetime import datetime
from werkzeug.utils import secure_filename
from database.db_manager import DatabaseManager
from database.init_db import init_database
from ai_security_layer import AISecurityLayer
import sys

# 设置UTF-8编码
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

app = Flask(__name__, static_folder='../frontend/dist', static_url_path='')
CORS(app)  # 允许跨域请求

# 配置
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), '..', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 初始化数据库
db = DatabaseManager()

# DeepSeek API配置
# 请在环境变量中设置DEEPSEEK_API_KEY，或直接替换下面的值
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')  # API密钥
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

# 初始化AI安全层
ai_security_layer = None

def init_ai_security_layer():
    global ai_security_layer
    if ai_security_layer is None:
        ai_security_layer = AISecurityLayer(db, DEEPSEEK_API_KEY, DEEPSEEK_API_URL)

# ==================== 前端页面路由 ====================
@app.route('/')
def index():
    """提供前端页面"""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def static_files(path):
    """提供静态文件"""
    try:
        return send_from_directory(app.static_folder, path)
    except:
        # 如果文件不存在，返回index.html（用于Vue Router的history模式）
        return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({"status": "ok", "message": "API服务正常运行"})

# ==================== 员工管理接口 ====================
@app.route('/api/employees', methods=['GET'])
def get_employees():
    """获取员工列表"""
    try:
        keyword = request.args.get('search', '')
        if keyword:
            employees = db.search_employees(keyword)
        else:
            employees = db.get_all_employees()
        return jsonify({"success": True, "data": employees})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/employees/<employee_id>', methods=['GET'])
def get_employee(employee_id):
    """获取单个员工信息"""
    try:
        employee = db.get_employee_by_id(employee_id)
        if employee:
            return jsonify({"success": True, "data": employee})
        else:
            return jsonify({"success": False, "message": "员工不存在"}), 404
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/employees', methods=['POST'])
def add_employee():
    """添加员工"""
    try:
        data = request.get_json()
        required_fields = ['employee_id', 'name', 'id_card', 'phone', 'bank_card', 'bank_name', 'position', 'status']
        
        for field in required_fields:
            if field not in data:
                return jsonify({"success": False, "message": f"缺少必填字段: {field}"}), 400
        
        db.add_employee(data)
        return jsonify({"success": True, "message": "员工添加成功"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/employees/<employee_id>', methods=['PUT'])
def update_employee(employee_id):
    """更新员工信息"""
    try:
        data = request.get_json()
        db.update_employee(employee_id, data)
        return jsonify({"success": True, "message": "员工信息更新成功"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/employees/<employee_id>', methods=['DELETE'])
def delete_employee(employee_id):
    """删除员工"""
    try:
        db.delete_employee(employee_id)
        return jsonify({"success": True, "message": "员工删除成功"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# ==================== 项目管理接口 ====================
@app.route('/api/projects', methods=['GET'])
def get_projects():
    """获取项目列表"""
    try:
        projects = db.get_all_projects()
        return jsonify({"success": True, "data": projects})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# ==================== 文件管理接口 ====================
@app.route('/api/files', methods=['GET'])
def get_files():
    """获取文件列表"""
    try:
        project_id = request.args.get('project_id')
        files = db.get_files_by_project(project_id)
        return jsonify({"success": True, "data": files})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/files/upload', methods=['POST'])
def upload_file():
    """上传文件"""
    try:
        if 'file' not in request.files:
            return jsonify({"success": False, "message": "没有选择文件"}), 400
        
        file = request.files['file']
        project_id = request.form.get('project_id')
        
        if file.filename == '':
            return jsonify({"success": False, "message": "文件名不能为空"}), 400
        
        if not project_id:
            return jsonify({"success": False, "message": "项目ID不能为空"}), 400
        
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        filename = timestamp + filename
        
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # 保存文件记录到数据库
        file_data = {
            'project_id': project_id,
            'file_name': file.filename,
            'file_path': file_path
        }
        db.add_file(file_data)
        
        return jsonify({"success": True, "message": "文件上传成功"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/files/download/<int:file_id>', methods=['GET'])
def download_file(file_id):
    """下载文件"""
    try:
        # 这里需要根据file_id查询文件路径
        # 简化实现，实际应该从数据库查询
        return jsonify({"success": False, "message": "下载功能待实现"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# ==================== 财务管理接口 ====================
@app.route('/api/salaries', methods=['GET'])
def get_salaries():
    """获取工资记录"""
    try:
        month = request.args.get('month')  # 格式: YYYY-MM
        salaries = db.get_salaries(month)
        return jsonify({"success": True, "data": salaries})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/expenses', methods=['GET'])
def get_expenses():
    """获取开销记录"""
    try:
        month = request.args.get('month')  # 格式: YYYY-MM
        expenses = db.get_expenses(month)
        return jsonify({"success": True, "data": expenses})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# ==================== 仪表盘接口 ====================
@app.route('/api/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """获取仪表盘统计数据"""
    try:
        stats = db.get_dashboard_stats()
        return jsonify({"success": True, "data": stats})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# ==================== AI对话接口 ====================
@app.route('/api/ai/chat', methods=['POST'])
def ai_chat():
    """智能AI对话接口"""
    try:
        # 初始化AI安全层
        if ai_security_layer is None:
            init_ai_security_layer()
        
        # 获取原始数据并确保正确的编码
        raw_data = request.get_data()
        print(f"[DEBUG] 原始请求数据: {repr(raw_data)}")
        
        try:
            # 尝试解码为UTF-8字符串
            if isinstance(raw_data, bytes):
                json_str = raw_data.decode('utf-8')
            else:
                json_str = str(raw_data)
            
            print(f"[DEBUG] 解码后的JSON字符串: {repr(json_str)}")
            
            # 解析JSON
            data = json.loads(json_str)
            user_message = data.get('message', '')
            
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            print(f"[DEBUG] 编码或JSON解析错误: {e}")
            # 回退到原来的方法
            data = request.get_json(force=True)
            user_message = data.get('message', '')
        
        print(f"[DEBUG] 接收到的用户消息: {repr(user_message)}")
        
        if not user_message:
            return jsonify({"success": False, "message": "消息不能为空"}), 400
        
        # 使用AI安全层处理用户消息
        ai_response = ai_security_layer.process_user_query(user_message)
        
        # 提取消息内容
        if isinstance(ai_response, dict):
            if ai_response.get('success', False):
                # 成功的情况，提取message或格式化data
                message = ai_response.get('message', '')
                data = ai_response.get('data', [])
                
                if data and isinstance(data, list):
                    # 如果有数据，格式化为表格
                    if len(data) > 0 and isinstance(data[0], dict):
                        # 构建表格格式的回复
                        headers = list(data[0].keys())
                        table_text = f"{message}\n\n"
                        
                        # 添加表头
                        table_text += " | ".join(headers) + "\n"
                        table_text += " | ".join(["---"] * len(headers)) + "\n"
                        
                        # 添加数据行
                        for row in data:
                            table_text += " | ".join([str(row.get(h, '')) for h in headers]) + "\n"
                        
                        response_message = table_text
                    else:
                        response_message = message
                else:
                    response_message = message
            else:
                # 失败的情况，返回错误消息
                response_message = ai_response.get('message', '处理失败')
        else:
            # 如果不是字典，直接转换为字符串
            response_message = str(ai_response)
        
        return jsonify({
            "success": True,
            "data": {
                "message": response_message,
                "timestamp": datetime.now().isoformat()
            }
        })
            
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

if __name__ == '__main__':
    # 初始化数据库
    init_database()
    print("数据库初始化完成")
    
    # 初始化AI安全层
    init_ai_security_layer()
    print("AI安全层初始化完成")
    
    # 启动Flask应用
    app.run(debug=True, host='0.0.0.0', port=5000)