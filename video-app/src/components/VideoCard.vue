<template>
  <div 
    class="video-card" 
    @click="handleClick"
    role="button"
    tabindex="0"
    :aria-label="`播放视频: ${video.video_title}`"
    @keydown.enter="handleClick"
    @keydown.space.prevent="handleClick"
  >
    <div class="thumbnail">
      <template v-if="video.video_image">
        <!-- Blurred backdrop fills the letterbox area behind the contained
             poster so non-16:9 covers look polished instead of showing a
             plain gradient. Hidden until the poster reports its real ratio. -->
        <img
          class="thumbnail-bg"
          ref="bgElement"
          alt=""
          aria-hidden="true"
        />
        <img
          class="thumbnail-img"
          ref="imgElement"
          :alt="video.video_title"
          @load="handleImageLoad"
          @error="handleImageError"
          loading="lazy"
        />
      </template>
      <div v-else class="placeholder" aria-hidden="true">
        <span>🎬</span>
      </div>
      <div class="placeholder" ref="placeholder" style="display: none;" aria-hidden="true">
        <span>🎬</span>
      </div>
      <div class="play-icon" aria-hidden="true">
        <span class="play-arrow"></span>
      </div>
      <div v-if="video.video_duration" class="duration">
        {{ video.video_duration }}
      </div>
    </div>
    <div class="info">
      <h3 class="title">{{ video.video_title }}</h3>
      <div class="meta">
        <span v-if="video.video_category" class="category">
          {{ video.video_category }}
        </span>
      </div>
      <div v-if="video.video_coins > 0" class="coins">
        <span class="coin-icon" aria-hidden="true">🪙</span>
        {{ video.video_coins }} 金币
      </div>
    </div>
  </div>
</template>

<script>
import { formatImageUrl, loadImageWithBase64Detection } from '@/utils/imageUtils'

export default {
  name: 'VideoCard',
  props: {
    video: {
      type: Object,
      required: true
    }
  },
  emits: ['click'],
  data() {
    return {
      lastLoadedUrl: null
    }
  },
  watch: {
    'video.video_image': {
      immediate: false,
      handler(newUrl) {
        if (newUrl && newUrl !== this.lastLoadedUrl) {
          this.loadImage()
        }
      }
    }
  },
  mounted() {
    this.loadImage()
  },
  methods: {
    handleClick() {
      this.$emit('click', this.video)
    },
    handleImageError(e) {
      e.target.style.display = 'none'
      if (this.$refs.bgElement) {
        this.$refs.bgElement.style.display = 'none'
      }
      if (this.$refs.placeholder) {
        this.$refs.placeholder.style.display = 'flex'
      }
    },
    handleImageLoad(e) {
      // Mirror the resolved poster src into the blurred backdrop so the
      // letterbox area around non-16:9 covers is filled with the same image.
      if (this.$refs.bgElement && e.target.src) {
        this.$refs.bgElement.src = e.target.src
      }
    },
    async loadImage() {
      const url = this.video?.video_image
      if (!url || !this.$refs.imgElement) return
      
      this.lastLoadedUrl = url
      await loadImageWithBase64Detection(this.$refs.imgElement, url)
    },
    // Use shared utility for formatting image URLs
    formatImageUrl
  }
}
</script>

<style scoped>
.video-card {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 15px;
  overflow: hidden;
  transition: all 0.3s ease;
  cursor: pointer;
  border: 1px solid rgba(255, 255, 255, 0.1);
  /* Remove default outline, we'll add custom focus style */
  outline: none;
}

.video-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
  border-color: #00d4ff;
}

/* Keyboard focus styling for accessibility */
.video-card:focus {
  border-color: #00d4ff;
  box-shadow: 0 0 0 3px rgba(0, 212, 255, 0.3);
}

.video-card:focus-visible {
  border-color: #00d4ff;
  box-shadow: 0 0 0 3px rgba(0, 212, 255, 0.3);
}

/* Touch device support - show play icon on touch */
.video-card:active .play-icon {
  opacity: 1;
}

.thumbnail {
  position: relative;
  width: 100%;
  padding-top: 56.25%; /* 16:9 aspect ratio */
  background: linear-gradient(135deg, #2a2a4a 0%, #1a1a3e 100%);
  overflow: hidden;
}

.thumbnail img {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

/* Foreground poster: cover fills the whole 16:9 frame so covers look full
   instead of letterboxed. */
.thumbnail-img {
  object-fit: cover;
  z-index: 1;
}

/* Blurred backdrop: a cover-fit, blurred copy of the same poster fills the
   letterbox gaps left by `contain` so non-16:9 covers look polished instead
   of showing a flat gradient. Scaled up slightly to hide blurred edges. */
.thumbnail-bg {
  object-fit: cover;
  filter: blur(18px) brightness(0.7) saturate(1.2);
  transform: scale(1.15);
  z-index: 0;
}

.placeholder {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 3em;
  color: #888;
}

.play-icon {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 50px;
  height: 50px;
  background: rgba(0, 212, 255, 0.9);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: all 0.3s;
  z-index: 2;
}

.video-card:hover .play-icon {
  opacity: 1;
}

.play-arrow {
  width: 0;
  height: 0;
  border-style: solid;
  border-width: 8px 0 8px 14px;
  border-color: transparent transparent transparent #fff;
  margin-left: 4px;
}

.duration {
  position: absolute;
  bottom: 8px;
  right: 8px;
  background: rgba(0, 0, 0, 0.7);
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  z-index: 2;
}

.info {
  padding: 15px;
}

.title {
  font-size: 1em;
  font-weight: 600;
  margin-bottom: 8px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: 1.4;
}

.meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 5px;
  font-size: 0.85em;
  color: #8b8b8b;
}

.category {
  background: rgba(0, 212, 255, 0.2);
  color: #00d4ff;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 0.75em;
}

.coins {
  margin-top: 8px;
  color: #ffd700;
  font-size: 0.85em;
  display: flex;
  align-items: center;
  gap: 4px;
}

.coin-icon {
  font-size: 1em;
}

/* Small mobile devices */
@media (max-width: 480px) {
  .video-card {
    border-radius: 10px;
  }
  
  .info {
    padding: 10px;
  }
  
  .title {
    font-size: 0.9em;
    margin-bottom: 5px;
  }
  
  .meta {
    font-size: 0.75em;
  }
  
  .category {
    padding: 2px 8px;
    font-size: 0.7em;
  }
  
  .play-icon {
    width: 40px;
    height: 40px;
  }
  
  .play-arrow {
    border-width: 6px 0 6px 10px;
  }
}

/* Tablet and small desktops */
@media (min-width: 481px) and (max-width: 1024px) {
  .info {
    padding: 12px;
  }
}

/* Large desktops */
@media (min-width: 1400px) {
  .info {
    padding: 18px;
  }
  
  .title {
    font-size: 1.1em;
  }
}
</style>
