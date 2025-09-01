<template>
  <div class="employees-container">
    <!-- 搜索和操作区域 -->
    <div class="search-container">
      <el-row :gutter="20" class="search-row">
        <el-col :xs="24" :sm="16" :md="18">
          <el-input
            v-model="searchKeyword"
            placeholder="请输入员工编号或姓名搜索"
            :prefix-icon="Search"
            @input="handleSearch"
            clearable
            class="search-input"
          />
        </el-col>
        <el-col :xs="24" :sm="8" :md="6">
          <el-button 
            type="primary" 
            :icon="Plus" 
            @click="showAddDialog"
            class="add-btn"
          >
            新增员工
          </el-button>
        </el-col>
      </el-row>
    </div>

    <!-- 员工列表 -->
    <div class="table-container">
      <el-table 
        :data="filteredEmployees" 
        v-loading="loading"
        stripe
        style="width: 100%"
        :header-cell-style="{ background: '#f5f7fa', color: '#333' }"
      >
        <el-table-column prop="employee_id" label="员工编号" width="120" />
        <el-table-column prop="name" label="姓名" width="100" />
        <el-table-column prop="position" label="职位" width="120" />
        <el-table-column prop="phone" label="电话号码" width="140" />
        <el-table-column prop="bank_name" label="开户行" width="120" />
        <el-table-column prop="status" label="在职状态" width="100">
          <template #default="{ row }">
            <el-tag 
              :type="getStatusType(row.status)"
              size="small"
            >
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button 
              type="primary" 
              size="small" 
              :icon="View"
              @click="viewEmployee(row)"
            >
              查看
            </el-button>
            <el-button 
              type="warning" 
              size="small" 
              :icon="Edit"
              @click="editEmployee(row)"
            >
              编辑
            </el-button>
            <el-button 
              type="danger" 
              size="small" 
              :icon="Delete"
              @click="deleteEmployee(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 新增/编辑员工对话框 -->
    <el-dialog 
      :title="dialogTitle"
      v-model="dialogVisible"
      width="600px"
      :before-close="handleDialogClose"
    >
      <el-form 
        :model="employeeForm" 
        :rules="formRules" 
        ref="employeeFormRef"
        label-width="100px"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="员工编号" prop="employee_id">
              <el-input 
                v-model="employeeForm.employee_id" 
                :disabled="isEdit"
                placeholder="请输入员工编号"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="姓名" prop="name">
              <el-input v-model="employeeForm.name" placeholder="请输入姓名" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="身份证号" prop="id_card">
              <el-input v-model="employeeForm.id_card" placeholder="请输入身份证号" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="电话号码" prop="phone">
              <el-input v-model="employeeForm.phone" placeholder="请输入电话号码" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="银行卡号" prop="bank_card">
              <el-input v-model="employeeForm.bank_card" placeholder="请输入银行卡号" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="开户行" prop="bank_name">
              <el-input v-model="employeeForm.bank_name" placeholder="请输入开户行" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="职位" prop="position">
              <el-input v-model="employeeForm.position" placeholder="请输入职位" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="在职状态" prop="status">
              <el-select v-model="employeeForm.status" placeholder="请选择状态">
                <el-option label="在职" value="在职" />
                <el-option label="离职" value="离职" />
                <el-option label="休假" value="休假" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="handleDialogClose">取消</el-button>
          <el-button type="primary" @click="submitForm" :loading="submitting">
            {{ isEdit ? '更新' : '添加' }}
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 查看员工详情对话框 -->
    <el-dialog 
      title="员工详情"
      v-model="viewDialogVisible"
      width="500px"
    >
      <div class="employee-detail" v-if="currentEmployee">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="员工编号">{{ currentEmployee.employee_id }}</el-descriptions-item>
          <el-descriptions-item label="姓名">{{ currentEmployee.name }}</el-descriptions-item>
          <el-descriptions-item label="身份证号">{{ currentEmployee.id_card }}</el-descriptions-item>
          <el-descriptions-item label="电话号码">{{ currentEmployee.phone }}</el-descriptions-item>
          <el-descriptions-item label="银行卡号">{{ currentEmployee.bank_card }}</el-descriptions-item>
          <el-descriptions-item label="开户行">{{ currentEmployee.bank_name }}</el-descriptions-item>
          <el-descriptions-item label="职位">{{ currentEmployee.position }}</el-descriptions-item>
          <el-descriptions-item label="在职状态">
            <el-tag :type="getStatusType(currentEmployee.status)">{{ currentEmployee.status }}</el-tag>
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Search, Plus, View, Edit, Delete 
} from '@element-plus/icons-vue'
import { apiService } from '../services/api'

// 响应式数据
const employees = ref([])
const searchKeyword = ref('')
const loading = ref(false)
const dialogVisible = ref(false)
const viewDialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const currentEmployee = ref(null)
const employeeFormRef = ref(null)

// 员工表单数据
const employeeForm = reactive({
  employee_id: '',
  name: '',
  id_card: '',
  phone: '',
  bank_card: '',
  bank_name: '',
  position: '',
  status: '在职'
})

// 表单验证规则
const formRules = {
  employee_id: [
    { required: true, message: '请输入员工编号', trigger: 'blur' }
  ],
  name: [
    { required: true, message: '请输入姓名', trigger: 'blur' }
  ],
  id_card: [
    { required: true, message: '请输入身份证号', trigger: 'blur' },
    { pattern: /^[1-9]\d{5}(18|19|20)\d{2}((0[1-9])|(1[0-2]))(([0-2][1-9])|10|20|30|31)\d{3}[0-9Xx]$/, message: '身份证号格式不正确', trigger: 'blur' }
  ],
  phone: [
    { required: true, message: '请输入电话号码', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '电话号码格式不正确', trigger: 'blur' }
  ],
  bank_card: [
    { required: true, message: '请输入银行卡号', trigger: 'blur' }
  ],
  bank_name: [
    { required: true, message: '请输入开户行', trigger: 'blur' }
  ],
  position: [
    { required: true, message: '请输入职位', trigger: 'blur' }
  ],
  status: [
    { required: true, message: '请选择在职状态', trigger: 'change' }
  ]
}

// 计算属性
const filteredEmployees = computed(() => {
  if (!searchKeyword.value) {
    return employees.value
  }
  return employees.value.filter(emp => 
    emp.name.includes(searchKeyword.value) || 
    emp.employee_id.includes(searchKeyword.value)
  )
})

const dialogTitle = computed(() => {
  return isEdit.value ? '编辑员工' : '新增员工'
})

// 方法
const loadEmployees = async () => {
  loading.value = true
  try {
    const response = await apiService.employees.getList()
    employees.value = response.data
  } catch (error) {
    console.error('加载员工列表失败:', error)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  // 搜索逻辑已在计算属性中实现
}

const getStatusType = (status) => {
  const statusMap = {
    '在职': 'success',
    '离职': 'danger',
    '休假': 'warning'
  }
  return statusMap[status] || 'info'
}

const showAddDialog = () => {
  isEdit.value = false
  resetForm()
  dialogVisible.value = true
}

const viewEmployee = (employee) => {
  currentEmployee.value = employee
  viewDialogVisible.value = true
}

const editEmployee = (employee) => {
  isEdit.value = true
  Object.assign(employeeForm, employee)
  dialogVisible.value = true
}

const deleteEmployee = async (employee) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除员工 "${employee.name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await apiService.employees.delete(employee.employee_id)
    ElMessage.success('删除成功')
    loadEmployees()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除员工失败:', error)
    }
  }
}

const resetForm = () => {
  Object.assign(employeeForm, {
    employee_id: '',
    name: '',
    id_card: '',
    phone: '',
    bank_card: '',
    bank_name: '',
    position: '',
    status: '在职'
  })
  if (employeeFormRef.value) {
    employeeFormRef.value.clearValidate()
  }
}

const handleDialogClose = () => {
  dialogVisible.value = false
  resetForm()
}

const submitForm = async () => {
  if (!employeeFormRef.value) return
  
  try {
    await employeeFormRef.value.validate()
    submitting.value = true
    
    if (isEdit.value) {
      await apiService.employees.update(employeeForm.employee_id, employeeForm)
      ElMessage.success('更新成功')
    } else {
      await apiService.employees.create(employeeForm)
      ElMessage.success('添加成功')
    }
    
    dialogVisible.value = false
    loadEmployees()
  } catch (error) {
    if (error.errors) {
      // 表单验证错误
      return
    }
    console.error('提交失败:', error)
  } finally {
    submitting.value = false
  }
}

// 组件挂载时加载数据
onMounted(() => {
  loadEmployees()
})
</script>

<style scoped>
.employees-container {
  padding: 20px;
  background: #f5f7fa;
  min-height: 100%;
}

.search-container {
  background: white;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.search-row {
  align-items: center;
}

.search-input {
  width: 100%;
}

.add-btn {
  width: 100%;
}

.table-container {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.employee-detail {
  padding: 10px 0;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .employees-container {
    padding: 10px;
  }
  
  .search-container {
    padding: 15px;
  }
  
  .table-container {
    padding: 15px;
    overflow-x: auto;
  }
  
  .search-row {
    flex-direction: column;
    gap: 10px;
  }
  
  .search-row .el-col {
    width: 100%;
  }
}
</style>