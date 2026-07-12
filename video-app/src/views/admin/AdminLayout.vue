<template>
  <div class="admin-layout">
    <!-- Sidebar -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <h1 class="admin-logo">🎬 管理后台</h1>
        <span v-if="isStandaloneMode" class="standalone-badge">独立模式</span>
      </div>
      
      <nav class="sidebar-nav">
        <router-link 
          v-for="item in menuItems" 
          :key="item.path"
          :to="item.path"
          class="nav-link"
          :class="{ active: isActive(item.path) }"
        >
          <span class="nav-icon">{{ item.icon }}</span>
          <span class="nav-text">{{ item.label }}</span>
        </router-link>
      </nav>
      
      <div class="sidebar-footer">
        <a v-if="isStandaloneMode" :href="frontendUrl" class="back-to-site">
          <span class="nav-icon">🏠</span>
          <span class="nav-text">返回前台</span>
        </a>
        <router-link v-else to="/" class="back-to-site">
          <span class="nav-icon">🏠</span>
          <span class="nav-text">返回前台</span>
        </router-link>
      </div>
    </aside>
    
    <!-- Main Content -->
    <main class="main-content">
      <header class="content-header">
        <h2 class="page-title">{{ currentPageTitle }}</h2>
      </header>
      
      <div class="content-body">
        <router-view />
      </div>
    </main>
  </div>
</template>

<script>
import { isStandaloneMode, getFrontendUrl, getAdminPath } from '@/utils/adminUtils'

export default {
  name: 'AdminLayout',
  computed: {
    // Use shared utility for standalone mode detection
    isStandaloneMode,
    menuItems() {
      return [
        { path: getAdminPath('dashboard'), icon: '📊', label: '仪表盘' },
        { path: getAdminPath('nav-categories'), icon: '📁', label: '导航分类管理' },
        { path: getAdminPath('video-management'), icon: '🎬', label: '视频管理' },
        { path: getAdminPath('collection'), icon: '📥', label: '视频采集' }
      ]
    },
    currentPageTitle() {
      const currentItem = this.menuItems.find(item => this.isActive(item.path))
      return currentItem ? currentItem.label : '管理后台'
    },
    frontendUrl() {
      return getFrontendUrl()
    }
  },
  methods: {
    isActive(path) {
      return this.$route.path === path || this.$route.path.startsWith(path + '/')
    }
  }
}
</script>

<style scoped>
.admin-layout {
  display: flex;
  min-height: 100vh;
  background: var(--admin-bg);
}

/* Sidebar */
.sidebar {
  width: 240px;
  background: var(--admin-surface);
  border-right: 1px solid var(--admin-border);
  box-shadow: var(--admin-shadow-sm);
  display: flex;
  flex-direction: column;
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  z-index: 100;
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid var(--admin-border);
}

.admin-logo {
  font-size: 1.3em;
  font-weight: 700;
  background: linear-gradient(90deg, var(--admin-accent-ink), var(--admin-primary));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0;
}

.standalone-badge {
  display: inline-block;
  margin-top: 8px;
  padding: 3px 8px;
  background: linear-gradient(135deg, #f59e0b, #fbbf24);
  border-radius: 10px;
  font-size: 0.7em;
  font-weight: 600;
  color: #fff;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.sidebar-nav {
  flex: 1;
  padding: 15px 10px;
  overflow-y: auto;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 15px;
  color: var(--admin-text-muted);
  text-decoration: none;
  border-radius: var(--admin-radius-sm);
  margin-bottom: 5px;
  transition: all 0.2s;
}

.nav-link:hover {
  background: var(--admin-surface-2);
  color: var(--admin-text);
}

.nav-link.active {
  background: var(--admin-primary-soft);
  color: var(--admin-primary-dark);
  border-left: 3px solid var(--admin-primary);
  font-weight: 600;
}

.nav-icon {
  font-size: 1.2em;
}

.nav-text {
  font-size: 0.95em;
  font-weight: 500;
}

.sidebar-footer {
  padding: 15px 10px;
  border-top: 1px solid var(--admin-border);
}

.back-to-site {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 15px;
  color: var(--admin-primary);
  text-decoration: none;
  border-radius: var(--admin-radius-sm);
  transition: all 0.2s;
}

.back-to-site:hover {
  background: var(--admin-primary-soft);
  color: var(--admin-primary-dark);
}

/* Main Content */
.main-content {
  flex: 1;
  margin-left: 240px;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.content-header {
  background: rgba(255, 255, 255, 0.85);
  padding: 20px 30px;
  border-bottom: 1px solid var(--admin-border);
  position: sticky;
  top: 0;
  z-index: 50;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.page-title {
  margin: 0;
  font-size: 1.4em;
  font-weight: 600;
  color: var(--admin-text);
}

.content-body {
  flex: 1;
  padding: 25px 30px;
  overflow-y: auto;
}

/* Mobile responsive */
@media (max-width: 768px) {
  .sidebar {
    width: 200px;
  }
  
  .main-content {
    margin-left: 200px;
  }
  
  .content-header {
    padding: 15px 20px;
  }
  
  .page-title {
    font-size: 1.2em;
  }
  
  .content-body {
    padding: 20px;
  }
}

@media (max-width: 576px) {
  .admin-layout {
    flex-direction: column;
  }
  
  .sidebar {
    width: 100%;
    position: relative;
    border-right: none;
    border-bottom: 1px solid var(--admin-border);
  }
  
  .sidebar-header {
    padding: 15px;
  }
  
  .sidebar-nav {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    padding: 10px;
  }
  
  .nav-link {
    padding: 8px 12px;
    margin-bottom: 0;
  }
  
  .sidebar-footer {
    display: none;
  }
  
  .main-content {
    margin-left: 0;
  }
  
  .content-header {
    padding: 12px 15px;
  }
  
  .content-body {
    padding: 15px;
  }
}
</style>
