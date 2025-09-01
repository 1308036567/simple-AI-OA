import { createRouter, createWebHistory } from 'vue-router'
import Layout from '../components/Layout.vue'
import AiChat from '../views/AiChat.vue'
import Dashboard from '../views/Dashboard.vue'
import Employees from '../views/Employees.vue'
import Files from '../views/Files.vue'
import Finance from '../views/Finance.vue'

const routes = [
  {
    path: '/',
    component: Layout,
    redirect: '/ai-chat',
    children: [
      {
        path: '/ai-chat',
        name: 'AiChat',
        component: AiChat,
        meta: { title: 'AI对话' }
      },
      {
        path: '/dashboard',
        name: 'Dashboard',
        component: Dashboard,
        meta: { title: '管理页面' }
      },
      {
        path: '/employees',
        name: 'Employees',
        component: Employees,
        meta: { title: '员工信息' }
      },
      {
        path: '/files',
        name: 'Files',
        component: Files,
        meta: { title: '文件信息' }
      },
      {
        path: '/finance',
        name: 'Finance',
        component: Finance,
        meta: { title: '财务信息' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router