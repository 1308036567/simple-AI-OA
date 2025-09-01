<template>
  <div class="ai-chat-container">
    <!-- 聊天消息区域 -->
    <div class="chat-messages" ref="messagesContainer">
      <div 
        v-for="(message, index) in messages" 
        :key="index" 
        :class="['message', message.type]"
      >
        <div class="message-content">
          <div class="message-text">{{ message.text }}</div>
          <div class="message-time">{{ formatTime(message.timestamp) }}</div>
        </div>
      </div>
      
      <!-- 加载状态 -->
      <div v-if="isLoading" class="message ai">
        <div class="message-content">
          <div class="message-text">
            <el-icon class="loading-icon"><Loading /></el-icon>
            AI正在思考中...
          </div>
        </div>
      </div>
    </div>

    <!-- 输入区域 -->
    <div class="chat-input-area">
      <div class="input-container">
        <el-input
          v-model="inputMessage"
          type="textarea"
          :rows="2"
          placeholder="请输入您的问题..."
          @keydown.enter.prevent="handleEnterKey"
          :disabled="isLoading"
          class="message-input"
        />
        <div class="input-actions">
          <el-upload
            :show-file-list="false"
            :before-upload="handleFileUpload"
            accept=".pdf,.doc,.docx,.txt,.xlsx,.xls"
          >
            <el-button :icon="Paperclip" circle :disabled="isLoading" />
          </el-upload>
          <el-button 
            type="primary" 
            :icon="Promotion" 
            @click="sendMessage"
            :loading="isLoading"
            :disabled="!inputMessage.trim()"
          >
            发送
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, nextTick, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading, Paperclip, Promotion } from '@element-plus/icons-vue'
import { apiService } from '../services/api'

// 响应式数据
const inputMessage = ref('')
const isLoading = ref(false)
const messagesContainer = ref(null)
const messages = reactive([
  {
    type: 'ai',
    text: '您好！我是您的AI助手，可以帮您查询员工信息、项目数据、财务记录等。请问有什么可以帮助您的吗？',
    timestamp: new Date()
  }
])

// 发送消息
const sendMessage = async () => {
  if (!inputMessage.value.trim() || isLoading.value) return

  const userMessage = inputMessage.value.trim()
  
  // 添加用户消息
  messages.push({
    type: 'user',
    text: userMessage,
    timestamp: new Date()
  })
  
  inputMessage.value = ''
  isLoading.value = true
  
  // 滚动到底部
  await nextTick()
  scrollToBottom()
  
  try {
    // 调用AI接口
    const response = await apiService.ai.chat(userMessage)
    
    // 添加AI回复
    messages.push({
      type: 'ai',
      text: response.data.message,
      timestamp: new Date()
    })
    
  } catch (error) {
    console.error('AI对话失败:', error)
    messages.push({
      type: 'ai',
      text: '抱歉，我暂时无法回答您的问题，请稍后再试。',
      timestamp: new Date()
    })
  } finally {
    isLoading.value = false
    await nextTick()
    scrollToBottom()
  }
}

// 处理回车键
const handleEnterKey = (event) => {
  if (event.ctrlKey || event.shiftKey) {
    // Ctrl+Enter 或 Shift+Enter 换行
    return
  }
  // 普通 Enter 发送消息
  sendMessage()
}

// 处理文件上传
const handleFileUpload = (file) => {
  ElMessage.info('文件上传功能开发中，敬请期待！')
  return false // 阻止自动上传
}

// 滚动到底部
const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// 格式化时间
const formatTime = (timestamp) => {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 组件挂载时滚动到底部
onMounted(() => {
  nextTick(() => {
    scrollToBottom()
  })
})
</script>

<style scoped>
.ai-chat-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message {
  display: flex;
  max-width: 70%;
}

.message.user {
  align-self: flex-end;
}

.message.ai {
  align-self: flex-start;
}

.message-content {
  background: white;
  border-radius: 12px;
  padding: 12px 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  position: relative;
}

.message.user .message-content {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.message.ai .message-content {
  background: white;
  color: #333;
}

.message-text {
  line-height: 1.5;
  word-wrap: break-word;
  white-space: pre-wrap;
}

.message-time {
  font-size: 12px;
  opacity: 0.7;
  margin-top: 4px;
  text-align: right;
}

.loading-icon {
  animation: spin 1s linear infinite;
  margin-right: 8px;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.chat-input-area {
  background: white;
  border-top: 1px solid #e4e7ed;
  padding: 20px;
}

.input-container {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.message-input {
  flex: 1;
}

.input-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

/* 滚动条样式 */
.chat-messages::-webkit-scrollbar {
  width: 6px;
}

.chat-messages::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 3px;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.3);
  border-radius: 3px;
}

.chat-messages::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.5);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .chat-messages {
    padding: 10px;
  }
  
  .message {
    max-width: 85%;
  }
  
  .chat-input-area {
    padding: 15px;
  }
  
  .input-container {
    flex-direction: column;
    gap: 10px;
  }
  
  .input-actions {
    align-self: flex-end;
  }
}
</style>