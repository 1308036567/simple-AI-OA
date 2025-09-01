<template>
  <div class="finance-container">
    <!-- 筛选区域 -->
    <div class="filter-container">
      <el-row :gutter="20" class="filter-row">
        <el-col :xs="24" :sm="12" :md="8">
          <el-date-picker
            v-model="selectedMonth"
            type="month"
            placeholder="选择月份筛选"
            format="YYYY年MM月"
            value-format="YYYY-MM"
            @change="handleMonthChange"
            clearable
            class="month-picker"
          />
        </el-col>
        <el-col :xs="24" :sm="12" :md="8">
          <el-select 
            v-model="activeTab" 
            placeholder="选择查看类型"
            @change="handleTabChange"
            class="tab-select"
          >
            <el-option label="工人工资" value="salaries" />
            <el-option label="项目开销" value="expenses" />
          </el-select>
        </el-col>
        <el-col :xs="24" :sm="24" :md="8">
          <el-button 
            type="primary" 
            :icon="Refresh"
            @click="refreshData"
            class="refresh-btn"
          >
            刷新数据
          </el-button>
        </el-col>
      </el-row>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-container">
      <el-row :gutter="20">
        <el-col :xs="24" :sm="12" :md="6">
          <div class="stat-card salary-card">
            <div class="stat-icon">
              <el-icon><Money /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">¥{{ formatMoney(salaryStats.total) }}</div>
              <div class="stat-label">工资总额</div>
            </div>
          </div>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <div class="stat-card paid-card">
            <div class="stat-icon">
              <el-icon><Check /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">¥{{ formatMoney(salaryStats.paid) }}</div>
              <div class="stat-label">已发工资</div>
            </div>
          </div>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <div class="stat-card unpaid-card">
            <div class="stat-icon">
              <el-icon><Close /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">¥{{ formatMoney(salaryStats.unpaid) }}</div>
              <div class="stat-label">未发工资</div>
            </div>
          </div>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <div class="stat-card expense-card">
            <div class="stat-icon">
              <el-icon><ShoppingCart /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">¥{{ formatMoney(expenseStats.total) }}</div>
              <div class="stat-label">开销总额</div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 数据表格 -->
    <div class="table-container">
      <!-- 工人工资表 -->
      <div v-if="activeTab === 'salaries'" class="salary-section">
        <div class="section-header">
          <h3>工人工资记录</h3>
          <p class="record-count">共 {{ salaries.length }} 条记录</p>
        </div>
        
        <el-table 
          :data="salaries" 
          v-loading="loading"
          stripe
          style="width: 100%"
          :header-cell-style="{ background: '#f5f7fa', color: '#333' }"
          :summary-method="getSalarySummary"
          show-summary
        >
          <el-table-column prop="employee_name" label="员工姓名" width="120" />
          <el-table-column prop="project_name" label="项目名称" width="150" />
          <el-table-column prop="amount" label="工资金额" width="120">
            <template #default="{ row }">
              <span class="amount-text">¥{{ formatMoney(row.amount) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="work_hours" label="工作时长" width="100">
            <template #default="{ row }">
              {{ row.work_hours }}小时
            </template>
          </el-table-column>
          <el-table-column prop="payment_status" label="发放状态" width="100">
            <template #default="{ row }">
              <el-tag 
                :type="row.payment_status === '已发' ? 'success' : 'warning'"
                size="small"
              >
                {{ row.payment_status }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="payment_date" label="发放时间" width="180">
            <template #default="{ row }">
              {{ formatDate(row.payment_date) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <el-button 
                v-if="row.payment_status === '未发'"
                type="success" 
                size="small" 
                :icon="Check"
                @click="markAsPaid(row)"
              >
                标记已发
              </el-button>
              <el-tag v-else type="success" size="small">已发放</el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 项目开销表 -->
      <div v-if="activeTab === 'expenses'" class="expense-section">
        <div class="section-header">
          <h3>项目开销记录</h3>
          <p class="record-count">共 {{ expenses.length }} 条记录</p>
        </div>
        
        <el-table 
          :data="expenses" 
          v-loading="loading"
          stripe
          style="width: 100%"
          :header-cell-style="{ background: '#f5f7fa', color: '#333' }"
          :summary-method="getExpenseSummary"
          show-summary
        >
          <el-table-column prop="project_name" label="项目名称" width="150" />
          <el-table-column prop="expense_type" label="开销类型" width="120">
            <template #default="{ row }">
              <el-tag 
                :type="getExpenseTypeColor(row.expense_type)"
                size="small"
              >
                {{ row.expense_type }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="unit" label="单位" width="80" />
          <el-table-column prop="quantity" label="数量" width="80" />
          <el-table-column prop="amount" label="金额" width="120">
            <template #default="{ row }">
              <span class="amount-text">¥{{ formatMoney(row.amount) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="expense_time" label="开销时间" width="180">
            <template #default="{ row }">
              {{ formatDate(row.expense_time) }}
            </template>
          </el-table-column>
          <el-table-column prop="description" label="备注" min-width="200" show-overflow-tooltip />
        </el-table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Refresh, Money, Check, Close, ShoppingCart 
} from '@element-plus/icons-vue'
import { apiService } from '../services/api'

// 响应式数据
const activeTab = ref('salaries')
const selectedMonth = ref('')
const loading = ref(false)
const salaries = ref([])
const expenses = ref([])

// 统计数据
const salaryStats = reactive({
  total: 0,
  paid: 0,
  unpaid: 0
})

const expenseStats = reactive({
  total: 0
})

// 监听月份变化
watch(selectedMonth, () => {
  refreshData()
})

// 方法
const loadSalaries = async () => {
  loading.value = true
  try {
    const params = selectedMonth.value ? { month: selectedMonth.value } : {}
    const response = await apiService.finance.getSalaries(params)
    salaries.value = response.data
    calculateSalaryStats()
  } catch (error) {
    console.error('加载工资数据失败:', error)
    ElMessage.error('加载工资数据失败')
  } finally {
    loading.value = false
  }
}

const loadExpenses = async () => {
  loading.value = true
  try {
    const params = selectedMonth.value ? { month: selectedMonth.value } : {}
    const response = await apiService.finance.getExpenses(params)
    expenses.value = response.data
    calculateExpenseStats()
  } catch (error) {
    console.error('加载开销数据失败:', error)
    ElMessage.error('加载开销数据失败')
  } finally {
    loading.value = false
  }
}

const calculateSalaryStats = () => {
  const total = salaries.value.reduce((sum, item) => sum + (item.amount || 0), 0)
  const paid = salaries.value
    .filter(item => item.payment_status === '已发')
    .reduce((sum, item) => sum + (item.amount || 0), 0)
  const unpaid = total - paid
  
  salaryStats.total = total
  salaryStats.paid = paid
  salaryStats.unpaid = unpaid
}

const calculateExpenseStats = () => {
  const total = expenses.value.reduce((sum, item) => sum + (item.amount || 0), 0)
  expenseStats.total = total
}

const refreshData = () => {
  if (activeTab.value === 'salaries') {
    loadSalaries()
  } else {
    loadExpenses()
  }
}

const handleMonthChange = () => {
  refreshData()
}

const handleTabChange = (tab) => {
  activeTab.value = tab
  refreshData()
}

const formatMoney = (amount) => {
  if (!amount && amount !== 0) return '0.00'
  return Number(amount).toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const getExpenseTypeColor = (type) => {
  const colorMap = {
    '材料采购': 'primary',
    '设备租赁': 'success',
    '人工支出': 'warning'
  }
  return colorMap[type] || 'info'
}

const getSalarySummary = (param) => {
  const { columns, data } = param
  const sums = []
  columns.forEach((column, index) => {
    if (index === 0) {
      sums[index] = '合计'
      return
    }
    if (column.property === 'amount') {
      const values = data.map(item => Number(item[column.property]))
      sums[index] = `¥${formatMoney(values.reduce((prev, curr) => prev + curr, 0))}`
    } else if (column.property === 'work_hours') {
      const values = data.map(item => Number(item[column.property]))
      sums[index] = `${values.reduce((prev, curr) => prev + curr, 0)}小时`
    } else {
      sums[index] = ''
    }
  })
  return sums
}

const getExpenseSummary = (param) => {
  const { columns, data } = param
  const sums = []
  columns.forEach((column, index) => {
    if (index === 0) {
      sums[index] = '合计'
      return
    }
    if (column.property === 'amount') {
      const values = data.map(item => Number(item[column.property]))
      sums[index] = `¥${formatMoney(values.reduce((prev, curr) => prev + curr, 0))}`
    } else if (column.property === 'quantity') {
      const values = data.map(item => Number(item[column.property]))
      sums[index] = values.reduce((prev, curr) => prev + curr, 0)
    } else {
      sums[index] = ''
    }
  })
  return sums
}

const markAsPaid = async (salary) => {
  try {
    await ElMessageBox.confirm(
      `确定要将 "${salary.employee_name}" 的工资标记为已发放吗？`,
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // 这里应该调用API更新工资状态
    // await apiService.finance.updateSalaryStatus(salary.id, '已发')
    
    // 临时更新本地数据
    salary.payment_status = '已发'
    salary.payment_date = new Date().toISOString()
    
    calculateSalaryStats()
    ElMessage.success('工资状态更新成功')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('更新工资状态失败:', error)
      ElMessage.error('更新工资状态失败')
    }
  }
}

// 组件挂载时加载数据
onMounted(() => {
  refreshData()
})
</script>

<style scoped>
.finance-container {
  padding: 20px;
  background: #f5f7fa;
  min-height: 100%;
}

.filter-container {
  background: white;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.filter-row {
  align-items: center;
}

.month-picker,
.tab-select {
  width: 100%;
}

.refresh-btn {
  width: 100%;
}

.stats-container {
  margin-bottom: 20px;
}

.stat-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  display: flex;
  align-items: center;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
}

.stat-icon {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 15px;
  font-size: 24px;
}

.salary-card .stat-icon {
  background: #e6f7ff;
  color: #1890ff;
}

.paid-card .stat-icon {
  background: #f6ffed;
  color: #52c41a;
}

.unpaid-card .stat-icon {
  background: #fff2e8;
  color: #fa8c16;
}

.expense-card .stat-icon {
  background: #f9f0ff;
  color: #722ed1;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.table-container {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.section-header {
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #ebeef5;
}

.section-header h3 {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 18px;
  font-weight: 600;
}

.record-count {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.amount-text {
  font-weight: 600;
  color: #f56c6c;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .finance-container {
    padding: 10px;
  }
  
  .filter-container {
    padding: 15px;
  }
  
  .table-container {
    padding: 15px;
    overflow-x: auto;
  }
  
  .filter-row {
    flex-direction: column;
    gap: 10px;
  }
  
  .filter-row .el-col {
    width: 100%;
  }
  
  .stat-card {
    margin-bottom: 10px;
  }
  
  .stat-value {
    font-size: 20px;
  }
}
</style>