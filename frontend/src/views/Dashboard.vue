<template>
  <div class="dashboard-container">
    <!-- 仪表盘统计区域 -->
    <div class="dashboard-stats">
      <h2 class="section-title">数据概览</h2>
      <el-row :gutter="20" class="stats-row">
        <!-- 员工统计 -->
        <el-col :xs="24" :sm="12" :md="6">
          <div class="stat-card employee-card">
            <div class="stat-icon">
              <el-icon size="40"><User /></el-icon>
            </div>
            <div class="stat-content">
              <h3>{{ stats.total_employees || 0 }}</h3>
              <p>员工总数</p>
              <div class="stat-detail">
                在职: {{ stats.active_employees || 0 }} 人
              </div>
            </div>
          </div>
        </el-col>

        <!-- 文件统计 -->
        <el-col :xs="24" :sm="12" :md="6">
          <div class="stat-card file-card">
            <div class="stat-icon">
              <el-icon size="40"><Document /></el-icon>
            </div>
            <div class="stat-content">
              <h3>{{ stats.total_files || 0 }}</h3>
              <p>文件总数</p>
              <div class="stat-detail">
                项目文件管理
              </div>
            </div>
          </div>
        </el-col>

        <!-- 工资统计 -->
        <el-col :xs="24" :sm="12" :md="6">
          <div class="stat-card salary-card">
            <div class="stat-icon">
              <el-icon size="40"><Money /></el-icon>
            </div>
            <div class="stat-content">
              <h3>¥{{ formatMoney(stats.total_salary) }}</h3>
              <p>工资总额</p>
              <div class="stat-detail">
                累计发放工资
              </div>
            </div>
          </div>
        </el-col>

        <!-- 开销统计 -->
        <el-col :xs="24" :sm="12" :md="6">
          <div class="stat-card expense-card">
            <div class="stat-icon">
              <el-icon size="40"><Wallet /></el-icon>
            </div>
            <div class="stat-content">
              <h3>¥{{ formatMoney(stats.total_expenses) }}</h3>
              <p>项目开销</p>
              <div class="stat-detail">
                累计项目支出
              </div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 功能卡片区域 -->
    <div class="function-cards">
      <h2 class="section-title">功能导航</h2>
      <el-row :gutter="20">
        <!-- 员工信息功能卡 -->
        <el-col :xs="24" :sm="12" :md="8">
          <div class="function-card" @click="navigateTo('/employees')">
            <div class="card-header">
              <el-icon size="30" class="card-icon"><UserFilled /></el-icon>
              <h3>员工信息管理</h3>
            </div>
            <div class="card-content">
              <p>管理员工基础信息，包括个人资料、职位、在职状态等</p>
              <ul>
                <li>员工信息查询</li>
                <li>新增员工档案</li>
                <li>编辑员工资料</li>
                <li>员工状态管理</li>
              </ul>
            </div>
            <div class="card-footer">
              <el-button type="primary" :icon="View">查看详情</el-button>
            </div>
          </div>
        </el-col>

        <!-- 文件信息功能卡 -->
        <el-col :xs="24" :sm="12" :md="8">
          <div class="function-card" @click="navigateTo('/files')">
            <div class="card-header">
              <el-icon size="30" class="card-icon"><FolderOpened /></el-icon>
              <h3>文件信息管理</h3>
            </div>
            <div class="card-content">
              <p>按项目分组管理文件，支持文件上传下载</p>
              <ul>
                <li>项目文件查看</li>
                <li>文件上传管理</li>
                <li>文件下载服务</li>
                <li>文件分类整理</li>
              </ul>
            </div>
            <div class="card-footer">
              <el-button type="primary" :icon="View">查看详情</el-button>
            </div>
          </div>
        </el-col>

        <!-- 财务信息功能卡 -->
        <el-col :xs="24" :sm="12" :md="8">
          <div class="function-card" @click="navigateTo('/finance')">
            <div class="card-header">
              <el-icon size="30" class="card-icon"><CreditCard /></el-icon>
              <h3>财务信息管理</h3>
            </div>
            <div class="card-content">
              <p>管理工人工资和项目开销，支持时间段筛选</p>
              <ul>
                <li>工资记录查询</li>
                <li>项目开销统计</li>
                <li>财务报表生成</li>
                <li>发放状态跟踪</li>
              </ul>
            </div>
            <div class="card-footer">
              <el-button type="primary" :icon="View">查看详情</el-button>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 项目文件统计 -->
    <div class="project-files" v-if="stats.project_files && stats.project_files.length > 0">
      <h2 class="section-title">项目文件统计</h2>
      <el-row :gutter="20">
        <el-col 
          v-for="project in stats.project_files" 
          :key="project.project_name"
          :xs="24" :sm="12" :md="8" :lg="6"
        >
          <div class="project-file-card">
            <div class="project-name">{{ project.project_name }}</div>
            <div class="file-count">{{ project.file_count }} 个文件</div>
          </div>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { 
  User, Document, Money, Wallet, UserFilled, 
  FolderOpened, CreditCard, View 
} from '@element-plus/icons-vue'
import { apiService } from '../services/api'

const router = useRouter()

// 响应式数据
const stats = reactive({
  total_employees: 0,
  active_employees: 0,
  total_files: 0,
  total_salary: 0,
  total_expenses: 0,
  project_files: []
})

const loading = ref(false)

// 导航到指定页面
const navigateTo = (path) => {
  router.push(path)
}

// 格式化金额
const formatMoney = (amount) => {
  if (!amount) return '0.00'
  return Number(amount).toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })
}

// 加载统计数据
const loadStats = async () => {
  loading.value = true
  try {
    const response = await apiService.dashboard.getStats()
    Object.assign(stats, response.data)
  } catch (error) {
    console.error('加载统计数据失败:', error)
    ElMessage.error('加载统计数据失败')
  } finally {
    loading.value = false
  }
}

// 组件挂载时加载数据
onMounted(() => {
  loadStats()
})
</script>

<style scoped>
.dashboard-container {
  padding: 20px;
  background: #f5f7fa;
  min-height: 100%;
  overflow-y: auto;
}

.section-title {
  font-size: 1.5em;
  color: #333;
  margin-bottom: 20px;
  font-weight: 600;
}

.dashboard-stats {
  margin-bottom: 30px;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  gap: 15px;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  cursor: pointer;
  height: 120px;
}

.stat-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.employee-card .stat-icon {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.file-card .stat-icon {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.salary-card .stat-icon {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.expense-card .stat-icon {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.stat-content {
  flex: 1;
}

.stat-content h3 {
  font-size: 2em;
  font-weight: bold;
  margin: 0 0 5px 0;
  color: #333;
}

.stat-content p {
  font-size: 1.1em;
  color: #666;
  margin: 0 0 5px 0;
}

.stat-detail {
  font-size: 0.9em;
  color: #999;
}

.function-cards {
  margin-bottom: 30px;
}

.function-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  cursor: pointer;
  height: 300px;
  display: flex;
  flex-direction: column;
  margin-bottom: 20px;
}

.function-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 15px;
  padding-bottom: 15px;
  border-bottom: 1px solid #eee;
}

.card-icon {
  color: #667eea;
}

.card-header h3 {
  margin: 0;
  color: #333;
  font-size: 1.2em;
}

.card-content {
  flex: 1;
  color: #666;
}

.card-content p {
  margin-bottom: 15px;
  line-height: 1.5;
}

.card-content ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.card-content li {
  padding: 5px 0;
  position: relative;
  padding-left: 15px;
}

.card-content li:before {
  content: '•';
  color: #667eea;
  position: absolute;
  left: 0;
}

.card-footer {
  padding-top: 15px;
  border-top: 1px solid #eee;
  text-align: center;
}

.project-files {
  margin-bottom: 30px;
}

.project-file-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  text-align: center;
  margin-bottom: 20px;
  transition: transform 0.3s ease;
}

.project-file-card:hover {
  transform: translateY(-3px);
}

.project-name {
  font-size: 1.1em;
  font-weight: 600;
  color: #333;
  margin-bottom: 10px;
}

.file-count {
  font-size: 1.5em;
  color: #667eea;
  font-weight: bold;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .dashboard-container {
    padding: 10px;
  }
  
  .stat-card {
    height: auto;
    min-height: 100px;
    flex-direction: column;
    text-align: center;
    gap: 10px;
  }
  
  .stat-icon {
    width: 50px;
    height: 50px;
  }
  
  .function-card {
    height: auto;
    min-height: 250px;
  }
  
  .section-title {
    font-size: 1.3em;
  }
}
</style>