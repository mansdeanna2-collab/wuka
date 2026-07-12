<template>
  <div class="dashboard">
    <!-- Hero banner -->
    <div class="dash-hero">
      <div class="hero-text">
        <h2 class="hero-title">欢迎回来 👋</h2>
        <p class="hero-sub">悟空视频管理后台 · 内容与分类一站式管理</p>
      </div>
      <div class="hero-actions">
        <router-link :to="getAdminPath('video-management')" class="hero-btn">
          <AppIcon name="film" :size="18" />
          <span>视频管理</span>
        </router-link>
        <router-link :to="getAdminPath('collection')" class="hero-btn ghost">
          <AppIcon name="download" :size="18" />
          <span>视频采集</span>
        </router-link>
      </div>
    </div>

    <!-- Statistics Cards -->
    <div class="stats-grid">
      <div class="stat-card" v-for="card in statCards" :key="card.label">
        <div class="stat-icon" :style="{ background: card.gradient }">
          <AppIcon :name="card.icon" :size="24" />
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ card.value }}</div>
          <div class="stat-label">{{ card.label }}</div>
        </div>
      </div>
    </div>
    
    <!-- Quick Links -->
    <div class="quick-links">
      <h3 class="section-title">快捷操作</h3>
      <div class="links-grid">
        <router-link :to="getAdminPath('nav-categories')" class="quick-link">
          <span class="link-icon"><AppIcon name="folder" :size="20" /></span>
          <span class="link-text">管理导航分类</span>
        </router-link>
        <router-link :to="getAdminPath('video-management')" class="quick-link">
          <span class="link-icon"><AppIcon name="film" :size="20" /></span>
          <span class="link-text">管理视频内容</span>
        </router-link>
        <a v-if="isStandaloneMode" :href="frontendUrl" class="quick-link">
          <span class="link-icon"><AppIcon name="globe" :size="20" /></span>
          <span class="link-text">查看前台效果</span>
        </a>
        <router-link v-else to="/" class="quick-link">
          <span class="link-icon"><AppIcon name="globe" :size="20" /></span>
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
            <span class="nav-name">
              <span class="nav-dot"></span>
              {{ navCat.label }}
            </span>
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
              <span
                v-if="(navCat.subcategories || []).length === 0"
                class="subcategory-empty"
              >
                暂无绑定分类
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
import { getNavCategories, fetchNavCategories } from '@/utils/navCategoryManager'
import { isStandaloneMode, getFrontendUrl, getAdminPath } from '@/utils/adminUtils'
import AppIcon from '@/components/AppIcon.vue'

export default {
  name: 'AdminDashboard',
  components: { AppIcon },
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
    statCards() {
      return [
        {
          icon: 'film',
          label: '视频总数',
          value: this.stats.total_videos || 0,
          gradient: 'linear-gradient(135deg, #7c3aed, #a855f7)'
        },
        {
          icon: 'folder',
          label: '视频分类',
          value: this.stats.total_categories || 0,
          gradient: 'linear-gradient(135deg, #0ea5e9, #38bdf8)'
        },
        {
          icon: 'link',
          label: '导航分类',
          value: this.navCategories.length,
          gradient: 'linear-gradient(135deg, #f59e0b, #fbbf24)'
        },
        {
          icon: 'layers',
          label: '已绑定分类',
          value: this.totalBoundCategories,
          gradient: 'linear-gradient(135deg, #16a34a, #4ade80)'
        }
      ]
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
      
      // Load navigation categories (fetch fresh from API, fall back to cache)
      try {
        this.navCategories = await fetchNavCategories()
      } catch (e) {
        console.error('Load nav categories error:', e)
        this.navCategories = getNavCategories()
      }
      this.loading = false
    }
  }
}
</script>

<style scoped>
.dashboard {
  max-width: 1200px;
}

/* Hero banner */
.dash-hero {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
  padding: 26px 30px;
  margin-bottom: 26px;
  border-radius: var(--admin-radius-lg);
  color: #fff;
  background: linear-gradient(135deg, #6d28d9 0%, #7c3aed 45%, #0ea5e9 100%);
  box-shadow: var(--admin-shadow);
}

.hero-title {
  margin: 0 0 6px 0;
  font-size: 1.5em;
  font-weight: 700;
}

.hero-sub {
  margin: 0;
  opacity: 0.9;
  font-size: 0.95em;
}

.hero-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.hero-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 18px;
  border-radius: var(--admin-radius-sm);
  background: rgba(255, 255, 255, 0.18);
  border: 1px solid rgba(255, 255, 255, 0.35);
  color: #fff;
  text-decoration: none;
  font-weight: 600;
  font-size: 0.9em;
  transition: all 0.2s;
}

.hero-btn:hover {
  background: rgba(255, 255, 255, 0.28);
  transform: translateY(-2px);
}

.hero-btn.ghost {
  background: rgba(255, 255, 255, 0.08);
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
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  border-radius: 14px;
  box-shadow: var(--admin-shadow-sm);
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
  display: inline-flex;
  align-items: center;
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
  transform: translateY(-2px);
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
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: var(--admin-text);
  font-size: 1.05em;
}

.nav-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--admin-primary), var(--admin-accent));
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

.subcategory-empty {
  font-size: 0.8em;
  color: var(--admin-text-faint);
}

/* Mobile responsive */
@media (max-width: 576px) {
  .dash-hero {
    padding: 20px;
  }

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
    width: 48px;
    height: 48px;
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
