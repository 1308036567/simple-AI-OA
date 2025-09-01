<template>
  <div class="layout">
    <!-- 顶部导航栏 -->
    <div class="header">
      <div class="header-left">
        <h1 class="title">公司信息管理系统</h1>
      </div>
      <div class="header-right">
        <el-button-group>
          <el-button 
            :type="currentRoute === '/ai-chat' ? 'primary' : 'default'"
            @click="navigateTo('/ai-chat')"
            :icon="ChatDotRound"
          >
            AI对话
          </el-button>
          <el-button 
            :type="currentRoute === '/dashboard' ? 'primary' : 'default'"
            @click="navigateTo('/dashboard')"
            :icon="DataBoard"
          >
            管理页面
          </el-button>
        </el-button-group>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="main-content">
      <router-view />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ChatDotRound, DataBoard } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()

const currentRoute = computed(() => route.path)

const navigateTo = (path) => {
  router.push(path)
}

onMounted(() => {
  // 页面加载时的初始化逻辑
})
</script>

<style scoped>
.layout {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: #f5f7fa;
}

.header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 0 20px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  position: relative;
  z-index: 1000;
}

.header-left .title {
  font-size: 1.5em;
  font-weight: bold;
  margin: 0;
}

.header-right {
  display: flex;
  align-items: center;
}

.main-content {
  flex: 1;
  overflow: hidden;
  position: relative;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .header {
    padding: 0 10px;
    height: 50px;
  }
  
  .header-left .title {
    font-size: 1.2em;
  }
  
  .header-right :deep(.el-button-group) {
    flex-direction: column;
  }
  
  .header-right :deep(.el-button) {
    font-size: 12px;
    padding: 5px 10px;
  }
}
</style>