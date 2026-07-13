<template>
  <div class="category-view">
    <!-- Fixed Top Bar: header + tag filter -->
    <div class="category-topbar">
      <!-- Category Header -->
      <header class="category-header">
        <button class="back-btn" @click="goBack" aria-label="返回">
          <AppIcon name="arrow-left" :size="20" />
        </button>
        <h1 class="category-title">{{ categoryName }}</h1>
        <div class="header-spacer"></div>
      </header>

      <!-- Tag Filter Bar -->
      <div v-if="showTagBar" class="tag-filter-bar">
        <button
          class="tag-chip"
          :class="{ active: selectedTag === '' }"
          @click="selectTag('')"
        >
          全部
        </button>
        <button
          v-for="tag in tags"
          :key="tag.tag"
          class="tag-chip"
          :class="{ active: selectedTag === tag.tag }"
          @click="selectTag(tag.tag)"
        >
          {{ tag.tag }}<span v-if="tag.count" class="tag-count">{{ tag.count }}</span>
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-state" :class="{ 'has-tagbar': showTagBar }">
      <div class="loading-spinner"></div>
      <p>加载中...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-state" :class="{ 'has-tagbar': showTagBar }">
      <div class="error-icon"><AppIcon name="alert" :size="40" :stroke-width="1.6" /></div>
      <p>{{ errorMessage }}</p>
      <button class="btn btn-primary" @click="loadVideos">重试</button>
    </div>

    <!-- Videos Grid -->
    <div v-else class="main-content" :class="{ 'has-tagbar': showTagBar }">
      <div class="videos-grid" v-if="videos.length > 0">
        <VideoCard
          v-for="video in videos"
          :key="video.video_id"
          :video="video"
          @click="playVideo"
        />
      </div>

      <!-- Empty State -->
      <div v-if="videos.length === 0 && !loading" class="empty-state">
        <div class="empty-icon">📹</div>
        <p>{{ selectedTag ? '该标签下暂无视频' : '该分类暂无视频' }}</p>
        <button v-if="selectedTag" class="btn btn-primary" @click="selectTag('')">查看全部</button>
        <button v-else class="btn btn-primary" @click="goBack">返回首页</button>
      </div>

      <!-- Load More -->
      <div v-if="hasMore || loadingMore" class="load-more">
        <button 
          class="btn btn-secondary" 
          @click="loadMore"
          :disabled="loadingMore"
        >
          <span v-if="loadingMore" class="loading-spinner small"></span>
          {{ loadingMore ? '加载中...' : '加载更多' }}
        </button>
      </div>
    </div>

    <!-- Bottom spacing for nav bar -->
    <div class="bottom-spacer"></div>
  </div>
</template>

<script>
import VideoCard from '@/components/VideoCard.vue'
import AppIcon from '@/components/AppIcon.vue'
import { videoApi } from '@/api'
import { extractArrayData } from '@/utils/apiUtils'
import { getMockVideosByCategory } from '@/utils/mockData'

export default {
  name: 'CategoryView',
  components: {
    VideoCard,
    AppIcon
  },
  data() {
    return {
      videos: [],
      tags: [],
      selectedTag: '',
      loading: true,
      loadingMore: false,
      error: false,
      errorMessage: '',
      page: 1,
      limit: 20,
      hasMore: true,
      usingMockData: false
    }
  },
  computed: {
    categoryName() {
      return this.$route.params.category || '分类'
    },
    showTagBar() {
      // Only show the filter bar when real tags exist for this category
      return !this.usingMockData && this.tags.length > 0
    }
  },
  watch: {
    '$route.params.category': {
      handler(newCategory) {
        if (newCategory) {
          this.selectedTag = ''
          this.loadTags()
          this.loadVideos()
        }
      }
    }
  },
  mounted() {
    this.loadTags()
    this.loadVideos()
  },
  methods: {
    goBack() {
      this.$router.push({ name: 'home' })
    },

    async loadTags() {
      this.tags = []
      try {
        const result = await videoApi.getCategoryTags(this.categoryName)
        const tags = extractArrayData(result)
        // Normalize: keep only entries that have a tag name
        this.tags = tags.filter(t => t && t.tag)
      } catch (e) {
        console.error('Load category tags error:', e)
        this.tags = []
      }
    },

    async loadVideos() {
      this.loading = true
      this.error = false
      this.page = 1
      this.videos = []
      
      try {
        const result = await videoApi.getVideosByCategory(
          this.categoryName, this.limit, 0, this.selectedTag)
        const videos = extractArrayData(result)
        
        if (videos.length === 0 && !this.selectedTag) {
          // Fallback to mock data (only for the unfiltered view)
          this.usingMockData = true
          this.videos = getMockVideosByCategory(this.categoryName, this.limit)
        } else {
          this.usingMockData = false
          this.videos = videos
        }
        
        this.hasMore = this.videos.length >= this.limit
      } catch (e) {
        console.error('Load category videos error:', e)
        if (this.selectedTag) {
          this.videos = []
          this.hasMore = false
        } else {
          // Fallback to mock data
          this.usingMockData = true
          this.videos = getMockVideosByCategory(this.categoryName, this.limit)
          this.hasMore = false
        }
      } finally {
        this.loading = false
      }
    },

    selectTag(tag) {
      if (this.selectedTag === tag) return
      this.selectedTag = tag
      this.loadVideos()
    },

    async loadMore() {
      if (this.loading || this.loadingMore) return
      
      // Mock data doesn't support pagination
      if (this.usingMockData) {
        this.hasMore = false
        return
      }
      
      this.loadingMore = true
      this.page++
      const offset = (this.page - 1) * this.limit
      
      try {
        const result = await videoApi.getVideosByCategory(
          this.categoryName, this.limit, offset, this.selectedTag)
        const newVideos = extractArrayData(result)
        this.videos = [...this.videos, ...newVideos]
        this.hasMore = newVideos.length >= this.limit
      } catch (e) {
        console.error('Load more error:', e)
      } finally {
        this.loadingMore = false
      }
    },
    
    playVideo(video) {
      this.$router.push({ name: 'player', params: { id: video.video_id } })
    }
  }
}
</script>

<style scoped>
.category-view {
  min-height: 100vh;
  padding: 0 15px;
  max-width: 1400px;
  margin: 0 auto;
}

/* Fixed Top Bar (header + tag filter) */
.category-topbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  background: rgba(26, 26, 46, 0.98);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

/* Category Header */
.category-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 15px;
}

/* Tag Filter Bar */
.tag-filter-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 15px 10px;
  overflow-x: auto;
  overflow-y: hidden;
  white-space: nowrap;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
}

.tag-filter-bar::-webkit-scrollbar {
  display: none;
}

.tag-chip {
  flex: 0 0 auto;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 14px;
  font-size: 0.85em;
  color: #cfcfcf;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.25s;
}

.tag-chip:hover {
  color: #fff;
  border-color: rgba(0, 212, 255, 0.4);
}

.tag-chip.active {
  color: #fff;
  background: linear-gradient(90deg, #00d4ff, #7c3aed);
  border-color: transparent;
}

.tag-count {
  font-size: 0.85em;
  opacity: 0.75;
}

.back-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 50%;
  color: #fff;
  font-size: 1.2em;
  cursor: pointer;
  transition: all 0.3s;
}

.back-btn:hover {
  background: rgba(0, 212, 255, 0.2);
  color: #00d4ff;
}

.category-title {
  flex: 1;
  text-align: center;
  font-size: 1.2em;
  font-weight: 600;
  color: #fff;
  margin: 0;
}

.header-spacer {
  width: 40px;
}

/* Main Content */
.main-content {
  padding-top: 80px;
  padding-bottom: 20px;
}

.main-content.has-tagbar {
  padding-top: 132px;
}

.loading-state.has-tagbar,
.error-state.has-tagbar {
  padding-top: 172px;
}

/* Videos Grid */
.videos-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

/* States */
.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 120px 20px;
  text-align: center;
}

.loading-state p,
.error-state p {
  margin-top: 15px;
  color: #888;
}

.error-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 84px;
  height: 84px;
  border-radius: 50%;
  color: #f59e0b;
  background: radial-gradient(circle at 50% 40%, rgba(245, 158, 11, 0.18), rgba(245, 158, 11, 0.04));
  border: 1px solid rgba(245, 158, 11, 0.25);
}

.error-state .btn {
  margin-top: 20px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
}

.empty-state .empty-icon {
  font-size: 4em;
  margin-bottom: 15px;
}

.empty-state p {
  color: #888;
  margin-bottom: 20px;
}

/* Load More */
.load-more {
  text-align: center;
  padding: 20px;
}

.load-more .btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.loading-spinner {
  width: 30px;
  height: 30px;
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: #00d4ff;
  animation: spin 1s ease-in-out infinite;
}

.loading-spinner.small {
  width: 16px;
  height: 16px;
  border-width: 2px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Button styles */
.btn {
  padding: 12px 24px;
  border: none;
  border-radius: 25px;
  font-size: 1em;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-primary {
  background: linear-gradient(90deg, #00d4ff, #7c3aed);
  color: #fff;
}

.btn-primary:hover {
  filter: brightness(1.1);
  transform: translateY(-2px);
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.2);
}

.btn-secondary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Bottom spacer for nav bar */
.bottom-spacer {
  height: 70px;
}

/* Mobile responsive */
@media (max-width: 768px) {
  .category-view {
    padding: 0 12px;
  }
  
  .category-header {
    padding: 10px 12px;
  }
  
  .back-btn {
    width: 36px;
    height: 36px;
    font-size: 1em;
  }
  
  .category-title {
    font-size: 1.1em;
  }
  
  .header-spacer {
    width: 36px;
  }
  
  .main-content {
    padding-top: 70px;
  }
  
  .main-content.has-tagbar {
    padding-top: 120px;
  }
  
  .loading-state.has-tagbar,
  .error-state.has-tagbar {
    padding-top: 160px;
  }
  
  .videos-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 15px;
  }
}

/* Small mobile devices */
@media (max-width: 480px) {
  .category-view {
    padding: 0 10px;
  }
  
  .category-header {
    padding: 10px;
  }
  
  .back-btn {
    width: 32px;
    height: 32px;
  }
  
  .category-title {
    font-size: 1em;
  }
  
  .header-spacer {
    width: 32px;
  }
  
  .main-content {
    padding-top: 65px;
  }
  
  .main-content.has-tagbar {
    padding-top: 113px;
  }
  
  .loading-state.has-tagbar,
  .error-state.has-tagbar {
    padding-top: 150px;
  }
  
  .videos-grid {
    gap: 10px;
  }
  
  .bottom-spacer {
    height: 60px;
  }
}

/* Large desktops */
@media (min-width: 1400px) {
  .category-view {
    max-width: 1600px;
    padding: 0 30px;
  }
  
  .category-header {
    padding: 15px 30px;
  }
  
  .category-title {
    font-size: 1.4em;
  }
}
</style>
