<template>
  <div class="player-view">
    <!-- Back button -->
    <div class="nav-bar">
      <button class="back-btn" @click="goBack" aria-label="返回">
        <AppIcon name="arrow-left" :size="22" />
      </button>
      <h2 class="title">{{ video.video_title || '视频播放' }}</h2>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-state">
      <div class="loading-spinner"></div>
      <p>加载中...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-state">
      <div class="error-icon"><AppIcon name="alert" :size="40" :stroke-width="1.6" /></div>
      <p>{{ errorMessage }}</p>
      <button class="btn btn-primary" @click="loadVideo">重试</button>
    </div>

    <!-- Video Player -->
    <div v-else class="player-container">
      <VideoPlayer
        ref="player"
        :src="video.video_url"
        :poster="video.video_image"
        :autoplay="true"
        @play="onPlay"
        @ended="onEnded"
      />
      
      <!-- Video Info -->
      <div class="video-info">
        <h1 class="video-title">{{ video.video_title }}</h1>
        
        <div class="video-meta">
          <span v-if="video.video_category" class="category">
            {{ video.video_category }}
          </span>
          <span v-if="video.play_count" class="play-count">
            {{ formatPlayCount(video.play_count) }} 次观看
          </span>
          <span v-if="video.upload_time" class="upload-time">
            {{ video.upload_time }}
          </span>
        </div>

        <div v-if="videoTags.length > 0" class="video-tags">
          <span
            v-for="tag in videoTags"
            :key="tag"
            class="video-tag"
          >{{ tag }}</span>
        </div>
        
        <div v-if="video.video_coins > 0" class="coins-info">
          <span class="coin-icon">🪙</span>
          需要 {{ video.video_coins }} 金币观看
        </div>
      </div>

      <!-- Related Videos -->
      <div v-if="relatedVideos.length > 0" class="related-section">
        <h3>相关视频</h3>
        <div class="related-grid">
          <VideoCard
            v-for="rv in relatedVideos"
            :key="rv.video_id"
            :video="rv"
            @click="playRelated"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import VideoPlayer from '@/components/VideoPlayer.vue'
import VideoCard from '@/components/VideoCard.vue'
import AppIcon from '@/components/AppIcon.vue'
import { videoApi } from '@/api'
import { formatPlayCount, isValidVideoUrl } from '@/utils/formatUtils'
import { extractArrayData, extractObjectData } from '@/utils/apiUtils'

export default {
  name: 'PlayerView',
  components: {
    VideoPlayer,
    VideoCard,
    AppIcon
  },
  data() {
    return {
      video: {},
      relatedVideos: [],
      loading: true,
      error: false,
      errorMessage: '',
      // Guard so play count is only reported once per loaded video, not on
      // every `play` event (resume-after-pause and seeking also fire `play`).
      hasCountedPlay: false
    }
  },
  computed: {
    // 视频标签: 后端以逗号分隔的字符串存储 (video_tags)
    videoTags() {
      const raw = this.video && this.video.video_tags
      if (!raw || typeof raw !== 'string') return []
      return raw
        .split(',')
        .map(t => t.trim())
        .filter(t => t.length > 0)
    }
  },
  watch: {
    '$route.params.id'(newId) {
      if (newId) {
        this.loadVideo()
      }
    }
  },
  mounted() {
    this.loadVideo()
  },
  methods: {
    async loadVideo() {
      const videoId = this.$route.params.id
      if (!videoId) {
        this.error = true
        this.errorMessage = '无效的视频ID'
        return
      }
      
      this.loading = true
      this.error = false
      // New video load: allow its play count to be reported once again.
      this.hasCountedPlay = false
      try {
        const result = await videoApi.getVideo(videoId)
        this.video = extractObjectData(result)
        
        if (!this.video.video_id) {
          this.error = true
          this.errorMessage = '视频不存在'
          return
        }
        
        // Validate video URL before playing
        if (!this.video.video_url || !isValidVideoUrl(this.video.video_url)) {
          console.warn('Invalid video URL:', this.video.video_url?.substring(0, 100))
          // Don't block - let VideoPlayer handle the error display
        }
        
        // Load related videos
        if (this.video.video_category) {
          this.loadRelatedVideos()
        }
      } catch (e) {
        this.error = true
        // Use user-friendly error message from API if available
        this.errorMessage = e.userMessage || '加载视频失败，请检查网络连接'
        console.error('Load video error:', e)
      } finally {
        this.loading = false
      }
    },
    
    async loadRelatedVideos() {
      try {
        // Use the new related videos API which already filters out the current video
        const result = await videoApi.getRelatedVideos(this.video.video_id, 6)
        this.relatedVideos = extractArrayData(result)
      } catch {
        // Fallback to category-based related videos if new API fails
        try {
          const result = await videoApi.getVideosByCategory(this.video.video_category, 6)
          const videos = extractArrayData(result)
          this.relatedVideos = videos.filter(v => v.video_id !== this.video.video_id)
        } catch (fallbackError) {
          console.error('Load related videos error:', fallbackError)
        }
      }
    },
    
    async onPlay() {
      // Only count a play once per loaded video. The <video> `play` event also
      // fires when resuming after a pause or after seeking, which previously
      // inflated the play count with duplicate requests.
      if (this.hasCountedPlay) return
      const videoId = this.video.video_id
      if (!videoId) return
      this.hasCountedPlay = true
      // Update play count with race condition protection
      try {
        await videoApi.updatePlayCount(videoId)
        // Only increment if we're still on the same video
        if (this.video.video_id === videoId && this.video.play_count) {
          this.video.play_count++
        }
      } catch (e) {
        // Allow a retry on the next play event if the request failed.
        this.hasCountedPlay = false
        console.error('Update play count error:', e)
      }
    },
    
    onEnded() {
      // Could auto-play next video
    },
    
    playRelated(video) {
      this.$router.push({ name: 'player', params: { id: video.video_id } })
    },
    
    goBack() {
      if (window.history.length > 1) {
        this.$router.back()
      } else {
        this.$router.push({ name: 'home' })
      }
    },
    
    // Use shared formatPlayCount from formatUtils
    formatPlayCount
  }
}
</script>

<style scoped>
.player-view {
  min-height: 100vh;
  background: #0a0a1a;
  /* Support for safe areas in landscape mode */
  padding-left: env(safe-area-inset-left);
  padding-right: env(safe-area-inset-right);
}

.nav-bar {
  display: flex;
  align-items: center;
  padding: 15px 20px;
  /* Support for iOS notch/safe areas */
  padding-top: calc(15px + env(safe-area-inset-top));
  padding-left: calc(20px + env(safe-area-inset-left));
  padding-right: calc(20px + env(safe-area-inset-right));
  background: rgba(0, 0, 0, 0.5);
  position: sticky;
  top: 0;
  z-index: 100;
}

.back-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  padding: 0;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 50%;
  color: #fff;
  cursor: pointer;
  transition: all 0.3s;
}

.back-btn:hover {
  background: rgba(0, 212, 255, 0.2);
  color: #00d4ff;
}

.nav-bar .title {
  flex: 1;
  text-align: center;
  font-size: 1em;
  font-weight: 500;
  color: #fff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin: 0 15px;
}

.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 100px 20px;
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

.player-container {
  max-width: 1200px;
  margin: 0 auto;
}

.video-info {
  padding: 20px;
}

.video-title {
  font-size: 1.3em;
  font-weight: 600;
  margin-bottom: 15px;
  color: #fff;
}

.video-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  font-size: 0.9em;
  color: #8b8b8b;
}

.category {
  background: rgba(0, 212, 255, 0.2);
  color: #00d4ff;
  padding: 4px 12px;
  border-radius: 20px;
}

.video-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.video-tag {
  font-size: 0.8em;
  color: #cfcfcf;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.12);
  padding: 3px 10px;
  border-radius: 14px;
}

.coins-info {
  margin-top: 15px;
  padding: 15px;
  background: rgba(255, 215, 0, 0.1);
  border: 1px solid rgba(255, 215, 0, 0.3);
  border-radius: 8px;
  color: #ffd700;
  display: flex;
  align-items: center;
  gap: 8px;
}

.coin-icon {
  font-size: 1.2em;
}

.related-section {
  padding: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.related-section h3 {
  margin-bottom: 15px;
  color: #fff;
  font-size: 1.1em;
}

.related-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 15px;
}

/* Mobile responsive */
@media (max-width: 768px) {
  .nav-bar {
    padding: 10px 15px;
    padding-top: calc(10px + env(safe-area-inset-top));
  }
  
  .video-info {
    padding: 15px;
  }
  
  .video-title {
    font-size: 1.1em;
  }
  
  .related-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
  }
}

/* Small mobile devices */
@media (max-width: 480px) {
  .nav-bar {
    padding: 8px 12px;
    padding-top: calc(8px + env(safe-area-inset-top));
  }
  
  .back-btn {
    width: 40px;
    height: 40px;
  }
  
  .nav-bar .title {
    font-size: 0.9em;
    margin: 0 10px;
  }
  
  .video-info {
    padding: 12px;
  }
  
  .video-title {
    font-size: 1em;
    margin-bottom: 10px;
  }
  
  .video-meta {
    gap: 10px;
    font-size: 0.8em;
  }
  
  .category {
    padding: 3px 10px;
  }
  
  .coins-info {
    margin-top: 12px;
    padding: 12px;
    font-size: 0.9em;
  }
  
  .related-section {
    padding: 15px 12px;
  }
  
  .related-section h3 {
    font-size: 1em;
    margin-bottom: 12px;
  }
  
  .related-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
  }
  
  .loading-state,
  .error-state {
    padding: 60px 15px;
  }
}

/* Landscape mobile */
@media (max-width: 768px) and (orientation: landscape) {
  .nav-bar {
    padding: 5px 15px;
  }
  
  .related-section {
    padding: 15px;
  }
  
  .related-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

/* Tablets */
@media (min-width: 769px) and (max-width: 1024px) {
  .related-grid {
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
  }
}

/* Large desktops */
@media (min-width: 1200px) {
  .player-container {
    max-width: 1400px;
    padding: 0 20px;
  }
  
  .video-info {
    padding: 25px 0;
  }
  
  .video-title {
    font-size: 1.5em;
  }
  
  .related-section {
    padding: 25px 0;
  }
  
  .related-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}
</style>
