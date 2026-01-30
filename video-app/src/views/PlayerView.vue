<template>
  <div class="player-view">
    <!-- Back button -->
    <div class="nav-bar">
      <button class="back-btn" @click="goBack">
        ← 返回
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
      <div class="error-icon">⚠️</div>
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
            {{ formatPlayCount(video.play_count) }} 次播放
          </span>
          <span v-if="video.upload_time" class="upload-time">
            {{ video.upload_time }}
          </span>
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
import { videoApi } from '@/api'

export default {
  name: 'PlayerView',
  components: {
    VideoPlayer,
    VideoCard
  },
  data() {
    return {
      video: {},
      relatedVideos: [],
      loading: true,
      error: false,
      errorMessage: ''
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
      
      try {
        const result = await videoApi.getVideo(videoId)
        this.video = result.data || result || {}
        
        if (!this.video.video_id) {
          this.error = true
          this.errorMessage = '视频不存在'
          return
        }
        
        // Load related videos
        if (this.video.video_category) {
          this.loadRelatedVideos()
        }
      } catch (e) {
        this.error = true
        this.errorMessage = '加载视频失败'
        console.error('Load video error:', e)
      } finally {
        this.loading = false
      }
    },
    
    async loadRelatedVideos() {
      try {
        const result = await videoApi.getVideosByCategory(this.video.video_category, 6)
        const videos = result.data || result || []
        // Filter out current video
        this.relatedVideos = videos.filter(v => v.video_id !== this.video.video_id)
      } catch (e) {
        console.error('Load related videos error:', e)
      }
    },
    
    async onPlay() {
      // Update play count
      try {
        await videoApi.updatePlayCount(this.video.video_id)
        if (this.video.play_count) {
          this.video.play_count++
        }
      } catch (e) {
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
    
    formatPlayCount(count) {
      if (count >= 10000) {
        return (count / 10000).toFixed(1) + '万'
      }
      return count.toString()
    }
  }
}
</script>

<style scoped>
.player-view {
  min-height: 100vh;
  background: #0a0a1a;
}

.nav-bar {
  display: flex;
  align-items: center;
  padding: 15px 20px;
  background: rgba(0, 0, 0, 0.5);
  position: sticky;
  top: 0;
  z-index: 100;
}

.back-btn {
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 6px;
  color: #fff;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
}

.back-btn:hover {
  background: rgba(255, 255, 255, 0.2);
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
  font-size: 4em;
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
</style>
