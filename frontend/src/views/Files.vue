<template>
  <div class="files-container">
    <!-- 操作区域 -->
    <div class="action-container">
      <el-row :gutter="20" class="action-row">
        <el-col :xs="24" :sm="16" :md="18">
          <el-select 
            v-model="selectedProject" 
            placeholder="选择项目查看文件"
            @change="handleProjectChange"
            clearable
            class="project-select"
          >
            <el-option 
              v-for="project in projects" 
              :key="project.project_id" 
              :label="project.project_name" 
              :value="project.project_id"
            />
          </el-select>
        </el-col>
        <el-col :xs="24" :sm="8" :md="6">
          <el-button 
            type="primary" 
            :icon="Upload" 
            @click="showUploadDialog"
            :disabled="!selectedProject"
            class="upload-btn"
          >
            上传文件
          </el-button>
        </el-col>
      </el-row>
    </div>

    <!-- 文件列表 -->
    <div class="files-content" v-if="selectedProject">
      <div class="project-info">
        <h3>{{ currentProjectName }} - 文件列表</h3>
        <p class="file-count">共 {{ files.length }} 个文件</p>
      </div>
      
      <div class="table-container">
        <el-table 
          :data="files" 
          v-loading="loading"
          stripe
          style="width: 100%"
          :header-cell-style="{ background: '#f5f7fa', color: '#333' }"
        >
          <el-table-column prop="file_id" label="文件编号" width="100" />
          <el-table-column prop="file_name" label="文件名" min-width="200">
            <template #default="{ row }">
              <el-link 
                type="primary" 
                @click="downloadFile(row)"
                :underline="false"
                class="file-link"
              >
                <el-icon><Document /></el-icon>
                {{ row.file_name }}
              </el-link>
            </template>
          </el-table-column>
          <el-table-column prop="file_path" label="文件路径" min-width="250" show-overflow-tooltip />
          <el-table-column prop="upload_time" label="上传时间" width="180">
            <template #default="{ row }">
              {{ formatDate(row.upload_time) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <el-button 
                type="primary" 
                size="small" 
                :icon="Download"
                @click="downloadFile(row)"
              >
                下载
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <!-- 空状态 -->
    <div class="empty-state" v-else>
      <el-empty description="请选择项目查看文件列表">
        <el-button type="primary" @click="loadProjects">刷新项目列表</el-button>
      </el-empty>
    </div>

    <!-- 上传文件对话框 -->
    <el-dialog 
      title="上传文件"
      v-model="uploadDialogVisible"
      width="500px"
      :before-close="handleUploadDialogClose"
    >
      <el-form 
        :model="uploadForm" 
        :rules="uploadRules" 
        ref="uploadFormRef"
        label-width="80px"
      >
        <el-form-item label="项目" prop="project_id">
          <el-select 
            v-model="uploadForm.project_id" 
            placeholder="选择项目"
            style="width: 100%"
            :disabled="!!selectedProject"
          >
            <el-option 
              v-for="project in projects" 
              :key="project.project_id" 
              :label="project.project_name" 
              :value="project.project_id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="文件" prop="file">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :on-change="handleFileChange"
            :on-remove="handleFileRemove"
            :file-list="fileList"
            :limit="1"
            drag
            class="upload-area"
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">
              将文件拖到此处，或<em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                支持上传任意格式文件，单个文件大小不超过 16MB
              </div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="handleUploadDialogClose">取消</el-button>
          <el-button 
            type="primary" 
            @click="submitUpload" 
            :loading="uploading"
            :disabled="!uploadForm.file"
          >
            上传
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Upload, Download, Document, UploadFilled 
} from '@element-plus/icons-vue'
import { apiService } from '../services/api'

// 响应式数据
const projects = ref([])
const files = ref([])
const selectedProject = ref('')
const loading = ref(false)
const uploadDialogVisible = ref(false)
const uploading = ref(false)
const fileList = ref([])
const uploadFormRef = ref(null)
const uploadRef = ref(null)

// 上传表单数据
const uploadForm = reactive({
  project_id: '',
  file: null
})

// 表单验证规则
const uploadRules = {
  project_id: [
    { required: true, message: '请选择项目', trigger: 'change' }
  ],
  file: [
    { required: true, message: '请选择文件', trigger: 'change' }
  ]
}

// 计算属性
const currentProjectName = computed(() => {
  const project = projects.value.find(p => p.project_id === selectedProject.value)
  return project ? project.project_name : ''
})

// 监听选中项目变化
watch(selectedProject, (newVal) => {
  if (newVal) {
    loadFiles(newVal)
  } else {
    files.value = []
  }
})

// 方法
const loadProjects = async () => {
  try {
    const response = await apiService.projects.getList()
    projects.value = response.data
  } catch (error) {
    console.error('加载项目列表失败:', error)
    ElMessage.error('加载项目列表失败')
  }
}

const loadFiles = async (projectId) => {
  loading.value = true
  try {
    const response = await apiService.files.getByProject(projectId)
    files.value = response.data
  } catch (error) {
    console.error('加载文件列表失败:', error)
    ElMessage.error('加载文件列表失败')
  } finally {
    loading.value = false
  }
}

const handleProjectChange = (projectId) => {
  selectedProject.value = projectId
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

const downloadFile = async (file) => {
  try {
    const response = await apiService.files.download(file.file_id)
    
    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', file.file_name)
    document.body.appendChild(link)
    link.click()
    
    // 清理
    window.URL.revokeObjectURL(url)
    document.body.removeChild(link)
    
    ElMessage.success('文件下载成功')
  } catch (error) {
    console.error('文件下载失败:', error)
    ElMessage.error('文件下载失败')
  }
}

const showUploadDialog = () => {
  uploadForm.project_id = selectedProject.value || ''
  uploadDialogVisible.value = true
}

const handleUploadDialogClose = () => {
  uploadDialogVisible.value = false
  resetUploadForm()
}

const resetUploadForm = () => {
  uploadForm.project_id = ''
  uploadForm.file = null
  fileList.value = []
  if (uploadFormRef.value) {
    uploadFormRef.value.clearValidate()
  }
}

const handleFileChange = (file, files) => {
  uploadForm.file = file.raw
  fileList.value = files
}

const handleFileRemove = () => {
  uploadForm.file = null
  fileList.value = []
}

const submitUpload = async () => {
  if (!uploadFormRef.value) return
  
  try {
    await uploadFormRef.value.validate()
    
    if (!uploadForm.file) {
      ElMessage.error('请选择文件')
      return
    }
    
    uploading.value = true
    
    const formData = new FormData()
    formData.append('file', uploadForm.file)
    formData.append('project_id', uploadForm.project_id)
    
    await apiService.files.upload(formData)
    
    ElMessage.success('文件上传成功')
    uploadDialogVisible.value = false
    
    // 如果当前选中的项目就是上传的项目，刷新文件列表
    if (selectedProject.value === uploadForm.project_id) {
      loadFiles(selectedProject.value)
    }
    
  } catch (error) {
    if (error.errors) {
      // 表单验证错误
      return
    }
    console.error('文件上传失败:', error)
    ElMessage.error('文件上传失败')
  } finally {
    uploading.value = false
  }
}

// 组件挂载时加载数据
onMounted(() => {
  loadProjects()
})
</script>

<style scoped>
.files-container {
  padding: 20px;
  background: #f5f7fa;
  min-height: 100%;
}

.action-container {
  background: white;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.action-row {
  align-items: center;
}

.project-select {
  width: 100%;
}

.upload-btn {
  width: 100%;
}

.files-content {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.project-info {
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #ebeef5;
}

.project-info h3 {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 18px;
  font-weight: 600;
}

.file-count {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.table-container {
  overflow-x: auto;
}

.file-link {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
}

.file-link:hover {
  color: #409eff;
}

.empty-state {
  background: white;
  border-radius: 8px;
  padding: 40px 20px;
  text-align: center;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.upload-area {
  width: 100%;
}

.upload-area :deep(.el-upload-dragger) {
  width: 100%;
  height: 120px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .files-container {
    padding: 10px;
  }
  
  .action-container {
    padding: 15px;
  }
  
  .files-content {
    padding: 15px;
  }
  
  .action-row {
    flex-direction: column;
    gap: 10px;
  }
  
  .action-row .el-col {
    width: 100%;
  }
  
  .table-container {
    overflow-x: auto;
  }
}
</style>