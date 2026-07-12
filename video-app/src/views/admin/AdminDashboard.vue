<template>
  <div class="dashboard">
    <!-- Statistics Cards -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon">📹</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.total_videos || 0 }}</div>
          <div class="stat-label">视频总数</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon">📁</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.total_categories || 0 }}</div>
          <div class="stat-label">视频分类</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon">🔗</div>
        <div class="stat-content">
          <div class="stat-value">{{ navCategories.length }}</div>
          <div class="stat-label">导航分类</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon">🎬</div>
        <div class="stat-content">
          <div class="stat-value">{{ totalBoundCategories }}</div>
          <div class="stat-label">已绑定分类</div>
        </div>
      </div>
    </div>
    
    <!-- Quick Links -->
    <div class="quick-links">
      <h3 class="section-title">快捷操作</h3>
      <div class="links-grid">
        <router-link :to="getAdminPath('nav-categories')" class="quick-link">
          <span class="link-icon">📁</span>
          <span class="link-text">管理导航分类</span>
        </router-link>
        <a v-if="isStandaloneMode" :href="frontendUrl" class="quick-link">
          <span class="link-icon">🌐</span>
          <span class="link-text">查看前台效果</span>
        </a>
        <router-link v-else to="/" class="quick-link">
          <span class="link-icon">🌐</span>
          <span class="link-text">查看前台效果</span>
        </router-link>
      </div>
    </div>
    
    <!-- Navigation Categories Overview -->
    <div class="nav-overview">
      <h3 class="section-title">导航分类概览</h3>
      <div class="nav-cards">
        <div 
          v-for="navCat in navCategories" 
          :key="navCat.key"
          class="nav-card"
        >
          <div class="nav-card-header">
            <span class="nav-name">{{ navCat.label }}</span>
            <span class="nav-count">{{ (navCat.subcategories || []).length }} 个分类</span>
          </div>
          <div class="nav-card-body">
            <div class="subcategory-tags">
              <span 
                v-for="sub in (navCat.subcategories || []).slice(0, 4)" 
                :key="sub"
                class="subcategory-tag"
              >
                {{ sub }}
              </span>
              <span 
                v-if="(navCat.subcategories || []).length > 4"
                class="subcategory-more"
              >
                +{{ (navCat.subcategories || []).length - 4 }} 更多
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { videoApi } from '@/api'
import { getNavCategories } from '@/utils/navCategoryManager'
import { isStandaloneMode, getFrontendUrl, getAdminPath } from '@/utils/adminUtils'

export default {
  name: 'AdminDashboard',
  data() {
    return {
      stats: {},
      navCategories: [],
      loading: true
    }
  },
  computed: {
    totalBoundCategories() {
      return this.navCategories.reduce((sum, nav) => sum + (nav.subcategories?.length || 0), 0)
    },
    // Use shared utility for standalone mode detection
    isStandaloneMode,
    frontendUrl() {
      return getFrontendUrl()
    }
  },
  mounted() {
    this.loadData()
  },
  methods: {
    // Use shared utility for admin path generation
    getAdminPath,
    async loadData() {
      this.loading = true
      try {
        // Load statistics from API
        const statsResult = await videoApi.getStatistics()
        if (statsResult && statsResult.data) {
          this.stats = statsResult.data
        }
      } catch (e) {
        console.error('Load statistics error:', e)
      }
      
      // Load navigation categories from local storage
      this.navCategories = getNavCategories()
      this.loading = false
    }
  }
}
</script>

<style scoped>
.dashboard {
  max-width: 1200px;
}

/* Statistics Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.stat-card {
  background: var(--admin-surface);
  border-radius: var(--admin-radius);
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 15px;
  border: 1px solid var(--admin-border);
  box-shadow: var(--admin-shadow-sm);
  transition: transform 0.3s, box-shadow 0.3s;
}

.stat-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--admin-shadow);
}

.stat-icon {
  font-size: 2.5em;
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--admin-primary-soft);
  border-radius: 12px;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 1.8em;
  font-weight: 700;
  color: var(--admin-text);
  line-height: 1.2;
}

.stat-label {
  font-size: 0.9em;
  color: var(--admin-text-muted);
  margin-top: 5px;
}

/* Section Title */
.section-title {
  font-size: 1.1em;
  font-weight: 600;
  color: var(--admin-text);
  margin: 0 0 15px 0;
  padding-left: 10px;
  border-left: 3px solid var(--admin-accent);
}

/* Quick Links */
.quick-links {
  margin-bottom: 30px;
}

.links-grid {
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
}

.quick-link {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 15px 20px;
  background: var(--admin-primary-soft);
  border: 1px solid var(--admin-primary-border);
  border-radius: var(--admin-radius);
  color: var(--admin-primary-dark);
  text-decoration: none;
  font-weight: 500;
  transition: all 0.2s;
}

.quick-link:hover {
  background: rgba(124, 58, 237, 0.16);
  transform: translateY(-2px);
  box-shadow: var(--admin-shadow-sm);
}

.link-icon {
  font-size: 1.3em;
}

.link-text {
  font-weight: 500;
}

/* Navigation Categories Overview */
.nav-overview {
  margin-bottom: 30px;
}

.nav-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 15px;
}

.nav-card {
  background: var(--admin-surface);
  border: 1px solid var(--admin-border);
  border-radius: var(--admin-radius);
  padding: 15px;
  box-shadow: var(--admin-shadow-sm);
  transition: all 0.2s;
}

.nav-card:hover {
  border-color: var(--admin-accent-border);
  box-shadow: var(--admin-shadow);
}

.nav-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--admin-border);
}

.nav-name {
  font-weight: 600;
  color: var(--admin-text);
  font-size: 1.05em;
}

.nav-count {
  font-size: 0.85em;
  color: var(--admin-primary);
}

.nav-card-body {
  min-height: 50px;
}

.subcategory-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.subcategory-tag {
  padding: 4px 10px;
  background: var(--admin-accent-soft);
  border: 1px solid var(--admin-accent-border);
  border-radius: 15px;
  font-size: 0.8em;
  color: var(--admin-accent-ink);
}

.subcategory-more {
  padding: 4px 10px;
  background: var(--admin-surface-3);
  border-radius: 15px;
  font-size: 0.8em;
  color: var(--admin-text-muted);
}

/* Mobile responsive */
@media (max-width: 576px) {
  .stats-grid {
    grid-template-columns: 1fr 1fr;
    gap: 12px;
  }
  
  .stat-card {
    padding: 15px;
    flex-direction: column;
    text-align: center;
    gap: 10px;
  }
  
  .stat-icon {
    font-size: 2em;
    width: 50px;
    height: 50px;
  }
  
  .stat-value {
    font-size: 1.5em;
  }
  
  .links-grid {
    flex-direction: column;
  }
  
  .nav-cards {
    grid-template-columns: 1fr;
  }
}
</style>
