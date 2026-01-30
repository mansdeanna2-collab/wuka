<template>
  <div class="video-player" ref="playerContainer">
    <div class="player-wrapper">
      <video
        ref="videoElement"
        :src="currentSrc"
        :poster="poster"
        controls
        playsinline
        webkit-playsinline
        x5-video-player-type="h5"
        x5-video-player-fullscreen="true"
        @play="onPlay"
        @pause="onPause"
        @ended="onEnded"
        @error="onError"
        @loadedmetadata="onLoadedMetadata"
        @timeupdate="onTimeUpdate"
      >
        您的浏览器不支持视频播放
      </video>
      
      <!-- Loading overlay -->
      <div v-if="loading" class="loading-overlay">
        <div class="loading-spinner"></div>
        <p>加载中...</p>
      </div>
      
      <!-- Error overlay -->
      <div v-if="error" class="error-overlay">
        <div class="error-icon">⚠️</div>
        <p>{{ errorMessage }}</p>
        <button class="btn btn-primary" @click="retry">重试</button>
      </div>
    </div>
    
    <!-- Episode selector if multiple sources -->
    <div v-if="episodes.length > 1" class="episode-list">
      <h4>选集</h4>
      <div class="episodes">
        <button
          v-for="(episode, index) in episodes"
          :key="index"
          :class="['episode-btn', { active: currentEpisode === index }]"
          @click="selectEpisode(index)"
        >
          {{ episode.name || `第${index + 1}集` }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'VideoPlayer',
  props: {
    src: {
      type: String,
      default: ''
    },
    poster: {
      type: String,
      default: ''
    },
    autoplay: {
      type: Boolean,
      default: false
    }
  },
  emits: ['play', 'pause', 'ended', 'error', 'time-update'],
  data() {
    return {
      loading: true,
      error: false,
      errorMessage: '',
      episodes: [],
      currentEpisode: 0,
      currentSrc: ''
    }
  },
  watch: {
    src: {
      immediate: true,
      handler(newSrc) {
        this.parseSource(newSrc)
      }
    }
  },
  methods: {
    parseSource(src) {
      if (!src) {
        this.currentSrc = ''
        this.episodes = []
        return
      }
      
      // Parse multiple episodes format: name1$url1#name2$url2
      if (src.includes('#')) {
        const parts = src.split('#')
        this.episodes = parts.map(part => {
          if (part.includes('$')) {
            const [name, url] = part.split('$')
            return { name, url }
          }
          return { name: '', url: part }
        })
        this.selectEpisode(0)
      } else if (src.includes('$')) {
        const [name, url] = src.split('$')
        this.episodes = [{ name, url }]
        this.currentSrc = url
      } else {
        this.episodes = [{ name: '', url: src }]
        this.currentSrc = src
      }
    },
    
    selectEpisode(index) {
      this.currentEpisode = index
      if (this.episodes[index]) {
        this.currentSrc = this.episodes[index].url
        this.loading = true
        this.error = false
        
        this.$nextTick(() => {
          if (this.$refs.videoElement) {
            this.$refs.videoElement.load()
            if (this.autoplay) {
              this.$refs.videoElement.play()
            }
          }
        })
      }
    },
    
    onPlay() {
      this.loading = false
      this.$emit('play')
    },
    
    onPause() {
      this.$emit('pause')
    },
    
    onEnded() {
      this.$emit('ended')
      // Auto play next episode
      if (this.currentEpisode < this.episodes.length - 1) {
        this.selectEpisode(this.currentEpisode + 1)
      }
    },
    
    onError(e) {
      this.loading = false
      this.error = true
      this.errorMessage = '视频加载失败，请稍后重试'
      this.$emit('error', e)
    },
    
    onLoadedMetadata() {
      this.loading = false
    },
    
    onTimeUpdate() {
      const video = this.$refs.videoElement
      if (video) {
        this.$emit('time-update', {
          currentTime: video.currentTime,
          duration: video.duration
        })
      }
    },
    
    retry() {
      this.error = false
      this.loading = true
      if (this.$refs.videoElement) {
        this.$refs.videoElement.load()
      }
    },
    
    // Public methods
    play() {
      if (this.$refs.videoElement) {
        this.$refs.videoElement.play()
      }
    },
    
    pause() {
      if (this.$refs.videoElement) {
        this.$refs.videoElement.pause()
      }
    },
    
    seek(time) {
      if (this.$refs.videoElement) {
        this.$refs.videoElement.currentTime = time
      }
    }
  }
}
</script>

<style scoped>
.video-player {
  width: 100%;
  background: #000;
  border-radius: 12px;
  overflow: hidden;
}

.player-wrapper {
  position: relative;
  width: 100%;
  padding-top: 56.25%; /* 16:9 aspect ratio */
}

.player-wrapper video {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: #000;
}

.loading-overlay,
.error-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.8);
  color: #fff;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: #00d4ff;
  animation: spin 1s ease-in-out infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.loading-overlay p,
.error-overlay p {
  margin-top: 15px;
  color: #888;
}

.error-icon {
  font-size: 3em;
  margin-bottom: 10px;
}

.error-overlay .btn {
  margin-top: 15px;
}

.episode-list {
  padding: 15px;
  background: rgba(255, 255, 255, 0.05);
}

.episode-list h4 {
  margin-bottom: 10px;
  color: #fff;
  font-size: 1em;
}

.episodes {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.episode-btn {
  padding: 8px 16px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.05);
  color: #fff;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
}

.episode-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: #00d4ff;
}

.episode-btn.active {
  background: linear-gradient(90deg, #00d4ff, #7c3aed);
  border-color: transparent;
}
</style>
