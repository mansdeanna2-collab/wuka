<template>
  <div class="page-container">
    <div class="page-header">
      <h1>{{ title }}</h1>
      <p class="subtitle">{{ subtitle }}</p>
    </div>

    <!-- Warning Banner -->
    <div class="warning-banner">
      <span class="warning-icon">⚠️</span>
      <span>仅供学习研究，请遵守当地法律法规</span>
    </div>
    
    <!-- Category Tabs -->
    <div class="category-tabs">
      <button 
        v-for="cat in categories" 
        :key="cat.id"
        :class="['tab-btn', { active: selectedCategory === cat.id }]"
        @click="selectedCategory = cat.id"
      >
        {{ cat.icon }} {{ cat.name }}
      </button>
    </div>

    <!-- Content Grid -->
    <div class="content-grid">
      <div 
        v-for="item in filteredContent" 
        :key="item.id" 
        class="content-card"
        @click="viewContent(item)"
      >
        <div class="card-icon">{{ item.icon }}</div>
        <div class="card-info">
          <h4>{{ item.title }}</h4>
          <p class="card-desc">{{ item.description }}</p>
          <div class="card-meta">
            <span :class="['status-badge', item.status]">{{ item.statusText }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Information Section -->
    <div class="info-section">
      <h3>📚 知识库</h3>
      <ul class="info-list">
        <li @click="showInfo('security')">
          <span class="info-icon">🔒</span>
          <span class="info-text">网络安全基础</span>
          <span class="info-arrow">→</span>
        </li>
        <li @click="showInfo('privacy')">
          <span class="info-icon">🕵️</span>
          <span class="info-text">隐私保护指南</span>
          <span class="info-arrow">→</span>
        </li>
        <li @click="showInfo('tools')">
          <span class="info-icon">🛠️</span>
          <span class="info-text">安全工具推荐</span>
          <span class="info-arrow">→</span>
        </li>
      </ul>
    </div>

    <!-- Toast Message -->
    <transition name="toast">
      <div v-if="toastMessage" class="toast-message">
        {{ toastMessage }}
      </div>
    </transition>
  </div>
</template>

<script>
export default {
  name: 'DarkWebView',
  data() {
    return {
      title: '暗网专区',
      subtitle: '探索未知领域',
      selectedCategory: 'all',
      toastMessage: '',
      categories: [
        { id: 'all', name: '全部', icon: '🌐' },
        { id: 'forum', name: '论坛', icon: '💬' },
        { id: 'resource', name: '资源', icon: '📦' },
        { id: 'tool', name: '工具', icon: '🛠️' }
      ],
      content: [
        { id: 1, title: '匿名交流社区', icon: '💬', category: 'forum', description: '安全匿名的讨论平台', status: 'coming', statusText: '即将上线' },
        { id: 2, title: '加密资源库', icon: '📦', category: 'resource', description: '加密存储与分享', status: 'coming', statusText: '即将上线' },
        { id: 3, title: 'Tor浏览器指南', icon: '🧅', category: 'tool', description: '洋葱网络入门教程', status: 'available', statusText: '可用' },
        { id: 4, title: 'VPN推荐', icon: '🛡️', category: 'tool', description: '安全VPN服务推荐', status: 'available', statusText: '可用' },
        { id: 5, title: '暗网市场分析', icon: '📊', category: 'forum', description: '暗网生态研究报告', status: 'coming', statusText: '即将上线' },
        { id: 6, title: '密码学基础', icon: '🔐', category: 'resource', description: '加密技术入门', status: 'available', statusText: '可用' }
      ]
    }
  },
  computed: {
    filteredContent() {
      if (this.selectedCategory === 'all') {
        return this.content
      }
      return this.content.filter(item => item.category === this.selectedCategory)
    }
  },
  methods: {
    viewContent(item) {
      if (item.status === 'coming') {
        this.showToast('该功能即将上线，敬请期待')
      } else {
        this.showToast(`正在打开: ${item.title}`)
      }
    },
    showInfo(type) {
      const titles = {
        security: '网络安全基础',
        privacy: '隐私保护指南',
        tools: '安全工具推荐'
      }
      this.showToast(`${titles[type]} 内容即将上线`)
    },
    showToast(message) {
      this.toastMessage = message
      setTimeout(() => {
        this.toastMessage = ''
      }, 2000)
    }
  }
}
</script>

<style scoped>
.page-container {
  min-height: 100vh;
  padding: 20px;
  padding-bottom: 80px;
}

.page-header {
  text-align: center;
  padding: 20px 0;
  margin-bottom: 15px;
}

.page-header h1 {
  font-size: 1.8em;
  margin-bottom: 10px;
  background: linear-gradient(90deg, #8b5cf6, #ec4899);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.subtitle {
  color: #888;
  font-size: 0.9em;
}

/* Warning Banner */
.warning-banner {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  background: rgba(255, 193, 7, 0.15);
  border: 1px solid rgba(255, 193, 7, 0.3);
  padding: 12px 20px;
  border-radius: 10px;
  margin-bottom: 20px;
  font-size: 0.85em;
  color: #ffc107;
}

.warning-icon {
  font-size: 1.2em;
}

/* Category Tabs */
.category-tabs {
  display: flex;
  gap: 10px;
  padding: 10px 0;
  overflow-x: auto;
  scrollbar-width: none;
  margin-bottom: 20px;
}

.category-tabs::-webkit-scrollbar {
  display: none;
}

.tab-btn {
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  color: #aaa;
  font-size: 0.9em;
  cursor: pointer;
  transition: all 0.3s;
  white-space: nowrap;
}

.tab-btn:hover {
  background: rgba(255, 255, 255, 0.15);
  color: #fff;
}

.tab-btn.active {
  background: linear-gradient(90deg, #8b5cf6, #ec4899);
  border-color: transparent;
  color: #fff;
}

/* Content Grid */
.content-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-bottom: 25px;
}

.content-card {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  padding: 15px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.content-card:hover {
  background: rgba(255, 255, 255, 0.1);
  transform: translateY(-3px);
  border-color: rgba(139, 92, 246, 0.5);
}

.card-icon {
  font-size: 2em;
  margin-bottom: 10px;
}

.card-info h4 {
  font-size: 0.95em;
  margin-bottom: 5px;
  color: #fff;
}

.card-desc {
  font-size: 0.75em;
  color: #888;
  margin-bottom: 8px;
}

.status-badge {
  font-size: 0.7em;
  padding: 3px 8px;
  border-radius: 10px;
}

.status-badge.available {
  background: rgba(34, 197, 94, 0.2);
  color: #22c55e;
}

.status-badge.coming {
  background: rgba(234, 179, 8, 0.2);
  color: #eab308;
}

/* Info Section */
.info-section {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 15px;
  padding: 15px;
}

.info-section h3 {
  font-size: 1em;
  margin-bottom: 12px;
  color: #fff;
}

.info-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.info-list li {
  display: flex;
  align-items: center;
  padding: 12px 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  cursor: pointer;
  transition: background 0.3s;
}

.info-list li:last-child {
  border-bottom: none;
}

.info-list li:hover {
  background: rgba(255, 255, 255, 0.05);
}

.info-icon {
  font-size: 1.2em;
  margin-right: 12px;
}

.info-text {
  flex: 1;
  font-size: 0.9em;
  color: #fff;
}

.info-arrow {
  color: #888;
}

/* Toast */
.toast-message {
  position: fixed;
  bottom: 100px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0, 0, 0, 0.85);
  color: #fff;
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 0.9em;
  z-index: 1000;
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(20px);
}

@media (max-width: 480px) {
  .page-header h1 {
    font-size: 1.4em;
  }
  
  .warning-banner {
    font-size: 0.75em;
    padding: 10px 15px;
  }
  
  .tab-btn {
    padding: 6px 12px;
    font-size: 0.8em;
  }
  
  .content-grid {
    gap: 8px;
  }
  
  .content-card {
    padding: 12px;
  }
  
  .card-icon {
    font-size: 1.6em;
  }
  
  .card-info h4 {
    font-size: 0.85em;
  }
}

@media (min-width: 768px) {
  .content-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}
</style>
