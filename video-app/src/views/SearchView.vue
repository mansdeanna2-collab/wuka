<template>
  <div class="search-page">
    <!-- Header with Back and Search -->
    <header class="header">
      <div class="header-content">
        <button class="back-btn" @click="goBack" aria-label="返回">
          <AppIcon name="arrow-left" :size="22" />
        </button>
        <div class="search-box">
          <AppIcon class="search-icon" name="search" :size="18" />
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
      <div v-if="searchKeyword && !loading && videos.length > 0" class="results-header">
        <div class="results-title">
          <span class="results-label">搜索结果</span>
          <span class="results-keyword">"{{ searchKeyword }}"</span>
        </div>
        <span class="results-count" v-if="videos.length > 0">{{ videos.length }} 个视频</span>
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
        <div class="empty-icon empty-icon--search">
          <span class="empty-icon-glow"></span>
          <AppIcon name="search" :size="44" :stroke-width="1.6" />
        </div>
        <h3 class="empty-title">未找到相关视频</h3>
        <p class="empty-desc">没有找到与 <b>"{{ searchKeyword }}"</b> 匹配的内容，换个关键词试试吧</p>
        <button class="btn btn-primary" @click="goBack">
          <AppIcon name="home" :size="18" />
          返回首页
        </button>
      </div>

      <!-- Initial State (no search yet) -->
      <div v-if="!loading && videos.length === 0 && !searchKeyword" class="empty-state">
        <div class="empty-icon empty-icon--initial">
          <span class="empty-icon-glow"></span>
          <AppIcon name="search" :size="44" :stroke-width="1.6" />
        </div>
        <h3 class="empty-title">发现精彩视频</h3>
        <p class="empty-desc">输入关键词，搜索你感兴趣的内容</p>
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
import AppIcon from '@/components/AppIcon.vue'
import { videoApi } from '@/api'
import { extractArrayData } from '@/utils/apiUtils'
import { searchMockVideos } from '@/utils/mockData'

export default {
  name: 'SearchView',
  components: {
    VideoCard,
    AppIcon
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
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  flex-shrink: 0;
  padding: 0;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 50%;
  color: #fff;
  cursor: pointer;
  transition: all 0.3s;
}

.back-btn:hover {
  background: rgba(0, 212, 255, 0.2);
  border-color: rgba(0, 212, 255, 0.4);
  color: #00d4ff;
}

.search-box {
  flex: 1;
  display: flex;
  align-items: center;
  max-width: 400px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 22px;
  padding-left: 14px;
  transition: border-color 0.25s, box-shadow 0.25s, background 0.25s;
}

.search-box:focus-within {
  background: rgba(255, 255, 255, 0.12);
  border-color: #7c3aed;
  box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.18);
}

.search-box .search-icon {
  color: #9aa;
  flex-shrink: 0;
  transition: color 0.25s;
}

.search-box:focus-within .search-icon {
  color: #a78bfa;
}

.search-box input {
  flex: 1;
  min-width: 0;
  padding: 8px 10px;
  border: none;
  border-radius: 0;
  background: transparent;
  color: #fff;
  font-size: 14px;
  outline: none;
}

.search-box input::placeholder {
  color: #888;
}

.search-btn {
  flex-shrink: 0;
  padding: 9px 20px;
  margin: 3px;
  background: linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%);
  border: none;
  border-radius: 18px;
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.25s, filter 0.2s;
}

.search-btn:hover {
  filter: brightness(1.08);
  box-shadow: 0 4px 14px rgba(124, 58, 237, 0.4);
}

.search-btn:active {
  transform: scale(0.96);
}

/* Main Content */
.main-content {
  padding-top: calc(80px + env(safe-area-inset-top));
}

/* Results Header */
.results-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 20px;
  padding-bottom: 14px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.results-title {
  display: flex;
  align-items: baseline;
  gap: 8px;
  font-size: 1.15em;
  font-weight: 600;
  color: #fff;
  min-width: 0;
}

.results-label {
  color: #cfd2e0;
  flex-shrink: 0;
}

.results-keyword {
  color: #a78bfa;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.results-count {
  font-size: 0.82em;
  color: #b9bcc9;
  font-weight: 500;
  padding: 4px 12px;
  background: rgba(124, 58, 237, 0.15);
  border: 1px solid rgba(124, 58, 237, 0.25);
  border-radius: 999px;
  flex-shrink: 0;
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
  min-height: 55vh;
  text-align: center;
  padding: 20px;
  animation: fadeInUp 0.5s ease both;
}

.empty-icon {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 110px;
  height: 110px;
  margin-bottom: 24px;
  border-radius: 50%;
  color: #a78bfa;
  background: radial-gradient(circle at 50% 40%, rgba(124, 58, 237, 0.22), rgba(124, 58, 237, 0.04));
  border: 1px solid rgba(124, 58, 237, 0.25);
  animation: floaty 4s ease-in-out infinite;
}

.empty-icon-glow {
  position: absolute;
  inset: -6px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(124, 58, 237, 0.35), transparent 70%);
  filter: blur(8px);
  opacity: 0.7;
  animation: pulse 2.6s ease-in-out infinite;
  z-index: -1;
}

.empty-icon--search {
  color: #00d4ff;
  background: radial-gradient(circle at 50% 40%, rgba(0, 212, 255, 0.18), rgba(0, 212, 255, 0.03));
  border-color: rgba(0, 212, 255, 0.25);
}

.empty-icon--search .empty-icon-glow {
  background: radial-gradient(circle, rgba(0, 212, 255, 0.3), transparent 70%);
}

.empty-title {
  font-size: 1.15em;
  font-weight: 600;
  color: #fff;
  margin: 0 0 8px;
}

.empty-desc {
  color: #9296a6;
  font-size: 0.92em;
  line-height: 1.6;
  max-width: 320px;
  margin: 0 0 24px;
}

.empty-desc b {
  color: #c9c2ff;
  font-weight: 600;
}

@keyframes floaty {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}

@keyframes pulse {
  0%, 100% { opacity: 0.4; transform: scale(1); }
  50% { opacity: 0.8; transform: scale(1.08); }
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(16px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Buttons */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 11px 24px;
  border: none;
  border-radius: 22px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.25s, filter 0.2s, background 0.25s;
}

.btn:active {
  transform: scale(0.96);
}

.btn-primary {
  background: linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%);
  color: #fff;
  box-shadow: 0 6px 18px rgba(124, 58, 237, 0.35);
}

.btn-primary:hover {
  filter: brightness(1.08);
  box-shadow: 0 8px 22px rgba(124, 58, 237, 0.45);
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
    width: 36px;
    height: 36px;
  }
  
  .search-box input {
    padding: 6px 8px;
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
