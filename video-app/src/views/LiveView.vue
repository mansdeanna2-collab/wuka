<template>
  <div class="page-container">
    <div class="page-header">
      <h1>{{ title }}</h1>
      <p class="subtitle">{{ subtitle }}</p>
    </div>
    
    <!-- Live Stream Categories -->
    <div class="category-tabs">
      <button 
        v-for="cat in categories" 
        :key="cat.id"
        :class="['tab-btn', { active: selectedCategory === cat.id }]"
        @click="selectedCategory = cat.id"
      >
        {{ cat.icon }} {{ cat.name }}
      </button>
    </div>

    <!-- Featured Live Stream -->
    <div v-if="featuredStream" class="featured-stream" @click="handleStreamClick">
      <div class="featured-thumbnail">
        <div class="live-badge">🔴 直播中</div>
        <div class="featured-overlay">
          <span class="viewers">{{ formatViewers(featuredStream.viewers) }}人观看</span>
        </div>
        <div class="featured-placeholder">
          <span class="stream-icon">{{ featuredStream.icon }}</span>
        </div>
      </div>
      <div class="featured-info">
        <h3>{{ featuredStream.title }}</h3>
        <p class="streamer">{{ featuredStream.streamer }}</p>
      </div>
    </div>

    <!-- Live Streams Grid -->
    <div class="streams-grid">
      <div 
        v-for="stream in filteredStreams" 
        :key="stream.id" 
        class="stream-card"
        @click="handleStreamClick"
      >
        <div class="stream-thumbnail">
          <div class="live-badge small">🔴</div>
          <div class="viewers-badge">{{ formatViewers(stream.viewers) }}</div>
          <div class="stream-placeholder">
            <span class="stream-icon">{{ stream.icon }}</span>
          </div>
        </div>
        <div class="stream-info">
          <h4>{{ stream.title }}</h4>
          <p class="streamer-name">{{ stream.streamer }}</p>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-if="filteredStreams.length === 0" class="empty-state">
      <div class="empty-icon">📺</div>
      <p>暂无直播</p>
      <p class="empty-hint">该分类暂时没有直播，请稍后再试</p>
    </div>

    <!-- Toast Message -->
    <transition name="toast">
      <div v-if="toastMessage" class="toast-message">
        {{ toastMessage }}
      </div>
    </transition>
  </div>
</template>

<script>
export default {
  name: 'LiveView',
  data() {
    return {
      title: '直播中心',
      subtitle: '精彩直播不间断',
      selectedCategory: 'all',
      toastMessage: '',
      categories: [
        { id: 'all', name: '全部', icon: '📺' },
        { id: 'hot', name: '热门', icon: '🔥' },
        { id: 'game', name: '游戏', icon: '🎮' },
        { id: 'music', name: '音乐', icon: '🎵' },
        { id: 'chat', name: '聊天', icon: '💬' }
      ],
      streams: [
        { id: 1, title: '王者荣耀大神直播', streamer: '电竞小王子', viewers: 12580, category: 'game', icon: '🎮' },
        { id: 2, title: '午夜音乐电台', streamer: 'DJ小白', viewers: 8920, category: 'music', icon: '🎵' },
        { id: 3, title: '和平精英吃鸡冲分', streamer: '狙击手阿杰', viewers: 6750, category: 'game', icon: '🎯' },
        { id: 4, title: '深夜聊天室', streamer: '知心姐姐', viewers: 4530, category: 'chat', icon: '💬' },
        { id: 5, title: '原神探索直播', streamer: '旅行者小琪', viewers: 3200, category: 'game', icon: '⚔️' },
        { id: 6, title: '钢琴即兴演奏', streamer: '琴师小雅', viewers: 2100, category: 'music', icon: '🎹' }
      ]
    }
  },
  computed: {
    featuredStream() {
      const filtered = this.selectedCategory === 'all' 
        ? this.streams 
        : this.streams.filter(s => s.category === this.selectedCategory)
      return filtered.length > 0 ? filtered[0] : null
    },
    filteredStreams() {
      const filtered = this.selectedCategory === 'all' 
        ? this.streams 
        : this.streams.filter(s => s.category === this.selectedCategory)
      // Exclude featured stream
      return filtered.slice(1)
    }
  },
  methods: {
    formatViewers(count) {
      if (count >= 10000) {
        return (count / 10000).toFixed(1) + '万'
      }
      return count.toString()
    },
    handleStreamClick() {
      this.showToast('直播功能即将上线，敬请期待')
    },
    showToast(message) {
      this.toastMessage = message
      setTimeout(() => {
        this.toastMessage = ''
      }, 2000)
    }
  }
}
</script>

<style scoped>
.page-container {
  min-height: 100vh;
  padding: 20px;
  padding-bottom: 80px;
}

.page-header {
  text-align: center;
  padding: 20px 0;
  margin-bottom: 15px;
}

.page-header h1 {
  font-size: 1.8em;
  margin-bottom: 10px;
  background: linear-gradient(90deg, #ff6b6b, #ffa502);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.subtitle {
  color: #888;
  font-size: 0.9em;
}

/* Category Tabs */
.category-tabs {
  display: flex;
  gap: 10px;
  padding: 10px 0;
  overflow-x: auto;
  scrollbar-width: none;
  margin-bottom: 20px;
}

.category-tabs::-webkit-scrollbar {
  display: none;
}

.tab-btn {
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  color: #aaa;
  font-size: 0.9em;
  cursor: pointer;
  transition: all 0.3s;
  white-space: nowrap;
}

.tab-btn:hover {
  background: rgba(255, 255, 255, 0.15);
  color: #fff;
}

.tab-btn.active {
  background: linear-gradient(90deg, #ff6b6b, #ffa502);
  border-color: transparent;
  color: #fff;
}

/* Featured Stream */
.featured-stream {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 15px;
  overflow: hidden;
  margin-bottom: 20px;
  cursor: pointer;
  transition: transform 0.3s, box-shadow 0.3s;
}

.featured-stream:hover {
  transform: translateY(-3px);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
}

.featured-thumbnail {
  position: relative;
  padding-top: 56.25%;
  background: linear-gradient(135deg, #2a2a4a 0%, #1a1a3e 100%);
}

.featured-placeholder {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stream-icon {
  font-size: 4em;
  opacity: 0.5;
}

.live-badge {
  position: absolute;
  top: 10px;
  left: 10px;
  background: rgba(255, 0, 0, 0.8);
  padding: 5px 10px;
  border-radius: 5px;
  font-size: 0.8em;
  font-weight: 600;
  z-index: 10;
  animation: pulse 2s infinite;
}

.live-badge.small {
  padding: 3px 6px;
  font-size: 0.7em;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.featured-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 15px;
  background: linear-gradient(transparent, rgba(0, 0, 0, 0.8));
}

.viewers {
  font-size: 0.9em;
  color: #fff;
}

.featured-info {
  padding: 15px;
}

.featured-info h3 {
  font-size: 1.1em;
  margin-bottom: 5px;
  color: #fff;
}

.streamer {
  color: #888;
  font-size: 0.85em;
}

/* Streams Grid */
.streams-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.stream-card {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.3s, box-shadow 0.3s;
}

.stream-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3);
}

.stream-thumbnail {
  position: relative;
  padding-top: 56.25%;
  background: linear-gradient(135deg, #2a2a4a 0%, #1a1a3e 100%);
}

.stream-placeholder {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stream-placeholder .stream-icon {
  font-size: 2.5em;
}

.viewers-badge {
  position: absolute;
  bottom: 8px;
  right: 8px;
  background: rgba(0, 0, 0, 0.7);
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 0.75em;
}

.stream-info {
  padding: 10px;
}

.stream-info h4 {
  font-size: 0.9em;
  margin-bottom: 4px;
  color: #fff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.streamer-name {
  font-size: 0.75em;
  color: #888;
}

/* Empty State */
.empty-state {
  text-align: center;
  padding: 40px 20px;
}

.empty-icon {
  font-size: 4em;
  margin-bottom: 15px;
}

.empty-state p {
  color: #888;
  margin-bottom: 5px;
}

.empty-hint {
  font-size: 0.85em;
  color: #666;
}

/* Toast */
.toast-message {
  position: fixed;
  bottom: 100px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0, 0, 0, 0.85);
  color: #fff;
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 0.9em;
  z-index: 1000;
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(20px);
}

@media (max-width: 480px) {
  .page-header h1 {
    font-size: 1.4em;
  }
  
  .tab-btn {
    padding: 6px 12px;
    font-size: 0.8em;
  }
  
  .streams-grid {
    gap: 8px;
  }
  
  .stream-info {
    padding: 8px;
  }
  
  .stream-info h4 {
    font-size: 0.8em;
  }
}

@media (min-width: 768px) {
  .streams-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (min-width: 1024px) {
  .streams-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}
</style>
