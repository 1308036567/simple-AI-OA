// 小微企业管理系统 - 前端应用（DeepSeek API集成版）
const { createApp } = Vue;
const { showToast, showDialog, showConfirmDialog, showNotify } = vant;

// API配置
const API_CONFIG = {
    baseURL: localStorage.getItem('serverUrl') || 'http://localhost:8000',
    timeout: 30000
};

// 创建axios实例
const api = axios.create({
    baseURL: API_CONFIG.baseURL,
    timeout: API_CONFIG.timeout,
    headers: {
        'Content-Type': 'application/json'
    }
});

// 请求拦截器
api.interceptors.request.use(
    config => {
        // 显示加载状态
        if (config.showLoading !== false) {
            app.globalLoading = true;
        }
        return config;
    },
    error => {
        app.globalLoading = false;
        return Promise.reject(error);
    }
);

// 响应拦截器
api.interceptors.response.use(
    response => {
        app.globalLoading = false;
        return response;
    },
    error => {
        app.globalLoading = false;
        
        let message = '网络错误';
        if (error.response) {
            message = error.response.data?.detail || error.response.data?.message || `请求失败 (${error.response.status})`;
        } else if (error.request) {
            message = '无法连接到服务器，请检查网络连接';
        }
        
        showNotify({ type: 'danger', message });
        return Promise.reject(error);
    }
);

// Vue应用
const app = createApp({
    data() {
        return {
            // 页面状态
            currentPage: 'home',
            globalLoading: false,
            
            // 通知状态
            showNotify: false,
            notifyType: 'success',
            notifyMessage: '',
            
            // 设置相关
            showSettings: false,
            showServerConfig: false,
            showVoiceConfig: false,
            showAbout: false,
            serverUrl: API_CONFIG.baseURL,
            tempServerUrl: API_CONFIG.baseURL,
            
            // 首页统计数据
            stats: {
                activeEmployees: 0,
                monthlySalary: 0,
                monthlyExpense: 0,
                totalFiles: 0
            },
            
            // 菜单项
            menuItems: [
                { id: 1, icon: 'chat-o', text: 'AI助手', page: 'chat', badge: 0 },
                { id: 2, icon: 'friends-o', text: '员工管理', page: 'employees' },
                { id: 3, icon: 'folder-o', text: '文件管理', page: 'files' },
                { id: 4, icon: 'bill-o', text: '账表管理', page: 'accounts' },
                { id: 5, icon: 'bar-chart-o', text: '数据统计', page: 'statistics' },
                { id: 6, icon: 'setting-o', text: '系统设置', page: 'settings' }
            ],
            
            // AI聊天相关
            chatMessages: [],
            inputMessage: '',
            isAiThinking: false,
            isRecording: false,
            unreadMessages: 0,
            currentSessionId: null,
            
            // 语音识别
            recognition: null,
            speechSynthesis: null,
            
            // 员工管理
            employees: [],
            employeeSearch: '',
            employeeFilter: 'all',
            employeeLoading: false,
            employeeFinished: false,
            employeePage: 1,
            showAddEmployee: false,
            
            // 文件管理
            files: [],
            fileCategory: 'all',
            fileCategoryOptions: [
                { text: '全部文件', value: 'all' },
                { text: '员工档案', value: 'employee_archive' },
                { text: '项目文档', value: 'project_document' },
                { text: '财务凭证', value: 'financial_voucher' },
                { text: '合同协议', value: 'contract' },
                { text: '其他文件', value: 'other' }
            ],
            fileLoading: false,
            fileFinished: false,
            filePage: 1,
            showUploadFile: false,
            
            // 账表管理
            accounts: [],
            accountLoading: false,
            accountFinished: false,
            accountPage: 1,
            showCreateAccount: false
        };
    },
    
    computed: {
        currentPageTitle() {
            const titles = {
                home: '小微企业管理系统',
                chat: 'AI智能助手',
                employees: '员工管理',
                files: '文件管理',
                accounts: '账表管理',
                statistics: '数据统计',
                settings: '系统设置'
            };
            return titles[this.currentPage] || '管理系统';
        }
    },
    
    watch: {
        currentPage(newPage) {
            // 页面切换时重置数据
            this.resetPageData(newPage);
            
            // 加载页面数据
            this.loadPageData(newPage);
        }
    },
    
    mounted() {
        // 初始化应用
        this.initApp();
        
        // 初始化语音识别
        this.initSpeechRecognition();
        
        // 加载首页数据
        this.loadHomeStats();
        
        // 检查服务器连接
        this.checkServerConnection();
    },
    
    methods: {
        // 初始化应用
        async initApp() {
            try {
                // 从本地存储恢复聊天记录
                const savedMessages = localStorage.getItem('chatMessages');
                if (savedMessages) {
                    this.chatMessages = JSON.parse(savedMessages);
                }
                
                // 生成会话ID
                this.currentSessionId = this.generateSessionId();
                
                console.log('应用初始化完成');
            } catch (error) {
                console.error('应用初始化失败:', error);
            }
        },
        
        // 检查服务器连接
        async checkServerConnection() {
            try {
                await api.get('/health', { showLoading: false });
                console.log('服务器连接正常');
            } catch (error) {
                console.warn('服务器连接失败:', error.message);
                showNotify({ 
                    type: 'warning', 
                    message: '无法连接到服务器，请检查服务器地址设置',
                    duration: 3000
                });
            }
        },
        
        // 导航相关
        navigateTo(page) {
            this.currentPage = page;
        },
        
        onNavBack() {
            if (this.currentPage !== 'home') {
                this.currentPage = 'home';
            }
        },
        
        // 重置页面数据
        resetPageData(page) {
            switch (page) {
                case 'employees':
                    this.employees = [];
                    this.employeePage = 1;
                    this.employeeFinished = false;
                    break;
                case 'files':
                    this.files = [];
                    this.filePage = 1;
                    this.fileFinished = false;
                    break;
                case 'accounts':
                    this.accounts = [];
                    this.accountPage = 1;
                    this.accountFinished = false;
                    break;
            }
        },
        
        // 加载页面数据
        async loadPageData(page) {
            switch (page) {
                case 'employees':
                    await this.loadEmployees();
                    break;
                case 'files':
                    await this.loadFiles();
                    break;
                case 'accounts':
                    await this.loadAccounts();
                    break;
            }
        },
        
        // 加载首页统计数据
        async loadHomeStats() {
            try {
                const response = await api.get('/api/dashboard/stats', { showLoading: false });
                this.stats = response.data;
            } catch (error) {
                console.error('加载统计数据失败:', error);
            }
        },
        
        // AI聊天相关方法
        async sendMessage() {
            if (!this.inputMessage.trim()) return;
            
            const userMessage = {
                type: 'user',
                content: this.inputMessage.trim(),
                timestamp: new Date()
            };
            
            this.chatMessages.push(userMessage);
            this.inputMessage = '';
            this.isAiThinking = true;
            
            // 滚动到底部
            this.$nextTick(() => {
                this.scrollToBottom();
            });
            
            try {
                const response = await api.post('/api/ai/chat', {
                    message: userMessage.content,
                    session_id: this.currentSessionId
                });
                
                const aiMessage = {
                    type: 'ai',
                    content: response.data.response,
                    timestamp: new Date()
                };
                
                this.chatMessages.push(aiMessage);
                
                // 保存聊天记录到本地存储
                this.saveChatMessages();
                
            } catch (error) {
                const errorMessage = {
                    type: 'ai',
                    content: '抱歉，我现在无法回应。请稍后再试。',
                    timestamp: new Date()
                };
                this.chatMessages.push(errorMessage);
            } finally {
                this.isAiThinking = false;
                this.$nextTick(() => {
                    this.scrollToBottom();
                });
            }
        },
        
        // 语音识别相关
        initSpeechRecognition() {
            if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
                const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                this.recognition = new SpeechRecognition();
                
                this.recognition.continuous = false;
                this.recognition.interimResults = false;
                this.recognition.lang = 'zh-CN';
                
                this.recognition.onresult = (event) => {
                    const transcript = event.results[0][0].transcript;
                    this.inputMessage = transcript;
                    showToast('语音识别完成');
                };
                
                this.recognition.onerror = (event) => {
                    console.error('语音识别错误:', event.error);
                    showToast('语音识别失败');
                    this.isRecording = false;
                };
                
                this.recognition.onend = () => {
                    this.isRecording = false;
                };
            } else {
                console.warn('浏览器不支持语音识别');
            }
        },
        
        startRecording() {
            if (!this.recognition) {
                showToast('浏览器不支持语音识别');
                return;
            }
            
            this.isRecording = true;
            this.recognition.start();
            showToast('开始语音识别...');
        },
        
        stopRecording() {
            if (this.recognition && this.isRecording) {
                this.recognition.stop();
            }
        },
        
        // 员工管理相关方法
        async loadEmployees() {
            if (this.employeeLoading || this.employeeFinished) return;
            
            this.employeeLoading = true;
            
            try {
                const params = {
                    page: this.employeePage,
                    size: 20,
                    search: this.employeeSearch || undefined,
                    is_archived: this.employeeFilter === 'archived' ? true : 
                                this.employeeFilter === 'active' ? false : undefined
                };
                
                const response = await api.get('/api/employees/', { params });
                const newEmployees = response.data.employees || [];
                
                if (this.employeePage === 1) {
                    this.employees = newEmployees;
                } else {
                    this.employees.push(...newEmployees);
                }
                
                this.employeePage++;
                this.employeeFinished = newEmployees.length < 20;
                
            } catch (error) {
                console.error('加载员工数据失败:', error);
            } finally {
                this.employeeLoading = false;
            }
        },
        
        async searchEmployees() {
            this.employeePage = 1;
            this.employeeFinished = false;
            this.employees = [];
            await this.loadEmployees();
        },
        
        async filterEmployees() {
            this.employeePage = 1;
            this.employeeFinished = false;
            this.employees = [];
            await this.loadEmployees();
        },
        
        viewEmployee(employee) {
            showDialog({
                title: employee.name,
                message: `
                    部门：${employee.department}\n
                    职位：${employee.position}\n
                    入职日期：${employee.hire_date}\n
                    状态：${employee.is_archived ? '已归档' : '在职'}
                `,
                confirmButtonText: '确定'
            });
        },
        
        editEmployee(employee) {
            showToast('编辑功能开发中...');
        },
        
        async archiveEmployee(employee) {
            try {
                await showConfirmDialog({
                    title: '确认归档',
                    message: `确定要归档员工 ${employee.name} 吗？`
                });
                
                await api.put(`/api/employees/${employee.id}/archive`);
                showToast('归档成功');
                
                // 刷新列表
                this.resetPageData('employees');
                await this.loadEmployees();
                
            } catch (error) {
                if (error !== 'cancel') {
                    console.error('归档员工失败:', error);
                }
            }
        },
        
        getAvatarUrl(name) {
            // 生成头像URL（使用第三方头像服务或默认头像）
            return `https://ui-avatars.com/api/?name=${encodeURIComponent(name)}&background=667eea&color=fff&size=64`;
        },
        
        // 文件管理相关方法
        async loadFiles() {
            if (this.fileLoading || this.fileFinished) return;
            
            this.fileLoading = true;
            
            try {
                const params = {
                    page: this.filePage,
                    size: 20,
                    category: this.fileCategory === 'all' ? undefined : this.fileCategory
                };
                
                const response = await api.get('/api/files/', { params });
                const newFiles = response.data.files || [];
                
                if (this.filePage === 1) {
                    this.files = newFiles;
                } else {
                    this.files.push(...newFiles);
                }
                
                this.filePage++;
                this.fileFinished = newFiles.length < 20;
                
            } catch (error) {
                console.error('加载文件数据失败:', error);
            } finally {
                this.fileLoading = false;
            }
        },
        
        async filterFiles() {
            this.filePage = 1;
            this.fileFinished = false;
            this.files = [];
            await this.loadFiles();
        },
        
        previewFile(file) {
            // 打开文件预览或下载
            const fileUrl = `${API_CONFIG.baseURL}/api/files/${file.id}/download`;
            window.open(fileUrl, '_blank');
        },
        
        getFileIcon(fileName) {
            const ext = fileName.split('.').pop().toLowerCase();
            const iconMap = {
                'pdf': '📄',
                'doc': '📝', 'docx': '📝',
                'xls': '📊', 'xlsx': '📊',
                'ppt': '📽️', 'pptx': '📽️',
                'jpg': '🖼️', 'jpeg': '🖼️', 'png': '🖼️', 'gif': '🖼️',
                'mp4': '🎬', 'avi': '🎬', 'mov': '🎬',
                'mp3': '🎵', 'wav': '🎵',
                'zip': '📦', 'rar': '📦', '7z': '📦',
                'txt': '📄'
            };
            return iconMap[ext] || '📄';
        },
        
        formatFileSize(bytes) {
            if (bytes === 0) return '0 B';
            const k = 1024;
            const sizes = ['B', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        },
        
        // 账表管理相关方法
        async loadAccounts() {
            if (this.accountLoading || this.accountFinished) return;
            
            this.accountLoading = true;
            
            try {
                const params = {
                    page: this.accountPage,
                    size: 20
                };
                
                const response = await api.get('/api/accounts/', { params });
                const newAccounts = response.data.accounts || [];
                
                if (this.accountPage === 1) {
                    this.accounts = newAccounts;
                } else {
                    this.accounts.push(...newAccounts);
                }
                
                this.accountPage++;
                this.accountFinished = newAccounts.length < 20;
                
            } catch (error) {
                console.error('加载账表数据失败:', error);
            } finally {
                this.accountLoading = false;
            }
        },
        
        viewAccount(account) {
            showToast('查看详情功能开发中...');
        },
        
        async exportAccount(account) {
            try {
                showToast('正在导出...');
                const response = await api.get(`/api/accounts/${account.id}/export`, {
                    responseType: 'blob'
                });
                
                // 创建下载链接
                const url = window.URL.createObjectURL(new Blob([response.data]));
                const link = document.createElement('a');
                link.href = url;
                link.setAttribute('download', `${account.table_name}.xlsx`);
                document.body.appendChild(link);
                link.click();
                link.remove();
                window.URL.revokeObjectURL(url);
                
                showToast('导出成功');
                
            } catch (error) {
                console.error('导出账表失败:', error);
            }
        },
        
        viewChart(account) {
            showToast('图表功能开发中...');
        },
        
        // 工具方法
        formatMessage(content) {
            // 简单的消息格式化（支持换行）
            return content.replace(/\n/g, '<br>');
        },
        
        formatTime(timestamp) {
            const date = new Date(timestamp);
            const now = new Date();
            const diff = now - date;
            
            if (diff < 60000) { // 1分钟内
                return '刚刚';
            } else if (diff < 3600000) { // 1小时内
                return Math.floor(diff / 60000) + '分钟前';
            } else if (diff < 86400000) { // 24小时内
                return Math.floor(diff / 3600000) + '小时前';
            } else {
                return date.toLocaleDateString() + ' ' + date.toLocaleTimeString().slice(0, 5);
            }
        },
        
        scrollToBottom() {
            const container = this.$refs.chatContainer;
            if (container) {
                container.scrollTop = container.scrollHeight;
            }
        },
        
        generateSessionId() {
            return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        },
        
        saveChatMessages() {
            try {
                localStorage.setItem('chatMessages', JSON.stringify(this.chatMessages));
            } catch (error) {
                console.error('保存聊天记录失败:', error);
            }
        },
        
        // 设置相关方法
        async saveServerConfig() {
            try {
                // 验证URL格式
                new URL(this.tempServerUrl);
                
                this.serverUrl = this.tempServerUrl;
                localStorage.setItem('serverUrl', this.serverUrl);
                
                // 更新axios配置
                api.defaults.baseURL = this.serverUrl;
                API_CONFIG.baseURL = this.serverUrl;
                
                showToast('服务器地址保存成功');
                this.showServerConfig = false;
                
                // 重新检查连接
                await this.checkServerConnection();
                
            } catch (error) {
                showToast('请输入有效的服务器地址');
            }
        },
        
        clearChatHistory() {
            showConfirmDialog({
                title: '确认清除',
                message: '确定要清除所有聊天记录吗？'
            }).then(() => {
                this.chatMessages = [];
                localStorage.removeItem('chatMessages');
                showToast('聊天记录已清除');
            }).catch(() => {
                // 用户取消
            });
        }
    }
});

// 使用Vant组件
app.use(vant);

// 挂载应用
app.mount('#app');

// 全局错误处理
window.addEventListener('error', (event) => {
    console.error('全局错误:', event.error);
});

window.addEventListener('unhandledrejection', (event) => {
    console.error('未处理的Promise拒绝:', event.reason);
});

// PWA支持
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then(registration => {
                console.log('SW registered: ', registration);
            })
            .catch(registrationError => {
                console.log('SW registration failed: ', registrationError);
            });
    });
}