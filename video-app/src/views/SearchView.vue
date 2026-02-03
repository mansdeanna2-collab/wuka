<template>
  <div class="search-page">
    <!-- Header with Back and Search -->
    <header class="header">
      <div class="header-content">
        <button class="back-btn" @click="goBack">
          ← 返回
        </button>
        <div class="search-box">
          <input
            v-model="searchKeyword"
            type="text"
            placeholder="搜索视频..."
            @keyup.enter="handleSearch"
            ref="searchInput"
          />
          <button class="search-btn" @click="handleSearch">搜索</button>
        </div>
      </div>
    </header>

    <!-- Loading State -->
    <div v-if="loading" class="loading-state">
      <div class="loading-spinner"></div>
      <p>搜索中...</p>
    </div>

    <!-- Search Results -->
    <div v-else class="main-content">
      <!-- Search Results Header -->
      <div v-if="searchKeyword && !loading" class="results-header">
        <h2 class="results-title">
          "{{ searchKeyword }}" 的搜索结果
          <span class="results-count" v-if="videos.length > 0">({{ videos.length }}个)</span>
        </h2>
      </div>

      <!-- Videos Grid -->
      <div v-if="videos.length > 0" class="videos-grid">
        <VideoCard
          v-for="video in videos"
          :key="video.video_id"
          :video="video"
          @click="playVideo"
        />
      </div>

      <!-- Empty State -->
      <div v-if="!loading && videos.length === 0 && searchKeyword" class="empty-state">
        <div class="empty-icon">🔍</div>
        <p>未找到 "{{ searchKeyword }}" 相关视频</p>
        <button class="btn btn-primary" @click="goBack">返回首页</button>
      </div>

      <!-- Initial State (no search yet) -->
      <div v-if="!loading && videos.length === 0 && !searchKeyword" class="empty-state">
        <div class="empty-icon">🎬</div>
        <p>请输入关键词搜索视频</p>
      </div>

      <!-- Load More -->
      <div v-if="hasMore && videos.length > 0" class="load-more">
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
import { videoApi } from '@/api'
import { extractArrayData } from '@/utils/apiUtils'
import { searchMockVideos } from '@/utils/mockData'

export default {
  name: 'SearchView',
  components: {
    VideoCard
  },
  data() {
    return {
      searchKeyword: '',
      videos: [],
      loading: false,
      loadingMore: false,
      page: 1,
      limit: 20,
      hasMore: true,
      usingMockData: false
    }
  },
  watch: {
    '$route.query.q'(newKeyword) {
      if (newKeyword && newKeyword !== this.searchKeyword) {
        this.searchKeyword = newKeyword
        this.handleSearch()
      }
    }
  },
  mounted() {
    // Get search keyword from route query
    if (this.$route.query.q) {
      this.searchKeyword = this.$route.query.q
      this.handleSearch()
    }
    // Focus search input
    this.$nextTick(() => {
      this.$refs.searchInput?.focus()
    })
  },
  methods: {
    goBack() {
      this.$router.push({ name: 'home' })
    },
    
    async handleSearch() {
      if (!this.searchKeyword.trim()) {
        return
      }
      
      this.loading = true
      this.page = 1
      this.videos = []
      
      try {
        const result = await videoApi.searchVideos(this.searchKeyword, this.limit)
        const videos = extractArrayData(result)
        
        if (videos.length === 0) {
          // Fallback to mock data
          this.videos = searchMockVideos(this.searchKeyword, this.limit)
          this.usingMockData = true
        } else {
          this.videos = videos
          this.usingMockData = false
        }
        
        this.hasMore = this.videos.length >= this.limit && !this.usingMockData
      } catch (e) {
        console.error('Search error:', e)
        // Fallback to mock data
        this.videos = searchMockVideos(this.searchKeyword, this.limit)
        this.usingMockData = true
        this.hasMore = false
      } finally {
        this.loading = false
      }
    },
    
    async loadMore() {
      if (this.loading || this.loadingMore || this.usingMockData) return
      
      this.loadingMore = true
      this.page++
      const offset = (this.page - 1) * this.limit
      
      try {
        const result = await videoApi.searchVideos(this.searchKeyword, this.limit, offset)
        const newVideos = extractArrayData(result)
        
        this.videos = [...this.videos, ...newVideos]
        this.hasMore = newVideos.length >= this.limit
      } catch (e) {
        console.error('Load more error:', e)
        this.hasMore = false
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
.search-page {
  min-height: 100vh;
  padding: 0 15px;
  max-width: 1400px;
  margin: 0 auto;
}

/* Header */
.header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  background: linear-gradient(180deg, rgba(26, 26, 46, 0.98) 0%, rgba(26, 26, 46, 0.95) 100%);
  padding: 12px 15px;
  padding-top: calc(12px + env(safe-area-inset-top));
  padding-left: calc(15px + env(safe-area-inset-left));
  padding-right: calc(15px + env(safe-area-inset-right));
  z-index: 100;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.header-content {
  display: flex;
  align-items: center;
  gap: 15px;
}

.back-btn {
  padding: 6px 12px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  color: #fff;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.3s;
  white-space: nowrap;
}

.back-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}

.search-box {
  flex: 1;
  display: flex;
  max-width: 400px;
}

.search-box input {
  flex: 1;
  padding: 8px 14px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 20px 0 0 20px;
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
  font-size: 14px;
  outline: none;
  transition: all 0.3s;
}

.search-box input:focus {
  border-color: #7c3aed;
  box-shadow: 0 0 10px rgba(124, 58, 237, 0.3);
}

.search-box input::placeholder {
  color: #888;
}

.search-btn {
  padding: 8px 18px;
  background: #7c3aed;
  border: none;
  border-radius: 0 20px 20px 0;
  color: #fff;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
}

.search-btn:hover {
  background: #6d28d9;
}

/* Main Content */
.main-content {
  padding-top: calc(80px + env(safe-area-inset-top));
}

/* Results Header */
.results-header {
  margin-bottom: 20px;
}

.results-title {
  font-size: 1.2em;
  font-weight: 600;
  color: #fff;
  margin: 0;
}

.results-count {
  font-size: 0.85em;
  color: #888;
  font-weight: 400;
  margin-left: 8px;
}

/* Videos Grid */
.videos-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 15px;
}

/* Loading State */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 50vh;
  padding-top: calc(80px + env(safe-area-inset-top));
}

.loading-state p {
  margin-top: 15px;
  color: #888;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: #00d4ff;
  animation: spin 1s ease-in-out infinite;
}

.loading-spinner.small {
  width: 16px;
  height: 16px;
  border-width: 2px;
  margin-right: 8px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Empty State */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 50vh;
  text-align: center;
}

.empty-icon {
  font-size: 4em;
  margin-bottom: 15px;
}

.empty-state p {
  color: #888;
  margin-bottom: 20px;
}

/* Buttons */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 10px 20px;
  border: none;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-primary {
  background: linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%);
  color: #fff;
}

.btn-primary:hover {
  background: linear-gradient(135deg, #8b47f5 0%, #7c3aed 100%);
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
  opacity: 0.5;
  cursor: not-allowed;
}

/* Load More */
.load-more {
  display: flex;
  justify-content: center;
  padding: 30px 0;
}

/* Bottom Spacer */
.bottom-spacer {
  height: calc(70px + env(safe-area-inset-bottom));
}

/* Mobile responsive */
@media (max-width: 480px) {
  .header-content {
    gap: 10px;
  }
  
  .back-btn {
    padding: 6px 10px;
    font-size: 12px;
  }
  
  .search-box input {
    padding: 6px 12px;
    font-size: 13px;
  }
  
  .search-btn {
    padding: 6px 14px;
    font-size: 13px;
  }
  
  .videos-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
  }
}
</style>
