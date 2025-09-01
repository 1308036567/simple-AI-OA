import axios from 'axios'
import { ElMessage } from 'element-plus'

// 创建axios实例
const api = axios.create({
  baseURL: 'http://localhost:5000/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    // 在发送请求之前做些什么
    return config
  },
  error => {
    // 对请求错误做些什么
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => {
    // 对响应数据做点什么
    const { data } = response
    if (data.success === false) {
      ElMessage.error(data.message || '请求失败')
      return Promise.reject(new Error(data.message || '请求失败'))
    }
    return data
  },
  error => {
    // 对响应错误做点什么
    const message = error.response?.data?.message || error.message || '网络错误'
    ElMessage.error(message)
    return Promise.reject(error)
  }
)

// API接口定义
export const apiService = {
  // 健康检查
  healthCheck() {
    return api.get('/health')
  },

  // 员工管理
  employees: {
    // 获取员工列表
    getList(params = {}) {
      return api.get('/employees', { params })
    },
    // 获取单个员工
    getById(id) {
      return api.get(`/employees/${id}`)
    },
    // 添加员工
    create(data) {
      return api.post('/employees', data)
    },
    // 更新员工
    update(id, data) {
      return api.put(`/employees/${id}`, data)
    },
    // 删除员工
    delete(id) {
      return api.delete(`/employees/${id}`)
    }
  },

  // 项目管理
  projects: {
    // 获取项目列表
    getList() {
      return api.get('/projects')
    }
  },

  // 文件管理
  files: {
    // 获取文件列表
    getList(params = {}) {
      return api.get('/files', { params })
    },
    // 上传文件
    upload(formData) {
      return api.post('/files/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
    },
    // 下载文件
    download(fileId) {
      return api.get(`/files/download/${fileId}`, {
        responseType: 'blob'
      })
    }
  },

  // 财务管理
  finance: {
    // 获取工资记录
    getSalaries(params = {}) {
      return api.get('/salaries', { params })
    },
    // 获取开销记录
    getExpenses(params = {}) {
      return api.get('/expenses', { params })
    }
  },

  // 仪表盘
  dashboard: {
    // 获取统计数据
    getStats() {
      return api.get('/dashboard/stats')
    }
  },

  // AI对话
  ai: {
    // 发送消息
    chat(message) {
      return api.post('/ai/chat', { message })
    }
  }
}

export default api