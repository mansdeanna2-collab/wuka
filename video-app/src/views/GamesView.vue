<template>
  <div class="page-container">
    <div class="page-header">
      <h1>{{ title }}</h1>
      <p class="subtitle">{{ subtitle }}</p>
    </div>
    
    <!-- Category Tabs -->
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

    <!-- Featured Game -->
    <div v-if="featuredGame" class="featured-game" @click="playGame(featuredGame)">
      <div class="featured-badge">🔥 热门推荐</div>
      <div class="featured-content">
        <div class="game-icon-large">{{ featuredGame.icon }}</div>
        <div class="featured-info">
          <h3>{{ featuredGame.name }}</h3>
          <p class="game-desc">{{ featuredGame.description }}</p>
          <div class="game-meta">
            <span class="rating">⭐ {{ featuredGame.rating }}</span>
            <span class="downloads">📥 {{ formatDownloads(featuredGame.downloads) }}</span>
          </div>
          <button class="play-btn" @click.stop="playGame(featuredGame)">
            立即试玩
          </button>
        </div>
      </div>
    </div>

    <!-- Games Grid -->
    <div class="games-grid">
      <div 
        v-for="game in filteredGames" 
        :key="game.id" 
        class="game-card"
        @click="playGame(game)"
      >
        <div class="game-icon">{{ game.icon }}</div>
        <div class="game-info">
          <h4>{{ game.name }}</h4>
          <p class="game-category">{{ game.categoryName }}</p>
          <div class="game-stats">
            <span class="rating">⭐ {{ game.rating }}</span>
          </div>
        </div>
        <button class="get-btn" @click.stop="playGame(game)">获取</button>
      </div>
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
  name: 'GamesView',
  data() {
    return {
      title: '游戏专区',
      subtitle: '精品游戏推荐',
      selectedCategory: 'all',
      toastMessage: '',
      categories: [
        { id: 'all', name: '全部', icon: '🎮' },
        { id: 'action', name: '动作', icon: '⚔️' },
        { id: 'puzzle', name: '益智', icon: '🧩' },
        { id: 'casual', name: '休闲', icon: '🎯' },
        { id: 'racing', name: '竞速', icon: '🏎️' }
      ],
      games: [
        { id: 1, name: '王者荣耀', icon: '👑', category: 'action', categoryName: '动作竞技', rating: 4.8, downloads: 5000000, description: '5V5 公平竞技手游，畅快对战' },
        { id: 2, name: '和平精英', icon: '🔫', category: 'action', categoryName: '射击对战', rating: 4.7, downloads: 4200000, description: '大逃杀类射击手游' },
        { id: 3, name: '开心消消乐', icon: '🍬', category: 'puzzle', categoryName: '益智消除', rating: 4.5, downloads: 3800000, description: '休闲益智消除游戏' },
        { id: 4, name: '跑跑卡丁车', icon: '🏎️', category: 'racing', categoryName: '竞速游戏', rating: 4.6, downloads: 2500000, description: '经典竞速手游' },
        { id: 5, name: '欢乐斗地主', icon: '🃏', category: 'casual', categoryName: '棋牌休闲', rating: 4.4, downloads: 6000000, description: '全民棋牌游戏' },
        { id: 6, name: '糖果传奇', icon: '🍭', category: 'puzzle', categoryName: '益智消除', rating: 4.3, downloads: 2100000, description: '甜蜜消除冒险' },
        { id: 7, name: '部落冲突', icon: '🏰', category: 'action', categoryName: '策略对战', rating: 4.6, downloads: 3200000, description: '策略塔防游戏' },
        { id: 8, name: '飞车竞速', icon: '🏁', category: 'racing', categoryName: '竞速游戏', rating: 4.2, downloads: 1800000, description: '极限赛车体验' }
      ]
    }
  },
  computed: {
    featuredGame() {
      return this.games[0]
    },
    filteredGames() {
      const filtered = this.selectedCategory === 'all' 
        ? this.games 
        : this.games.filter(g => g.category === this.selectedCategory)
      // Exclude featured game
      return filtered.slice(1)
    }
  },
  methods: {
    formatDownloads(count) {
      if (count >= 10000) {
        return (count / 10000).toFixed(0) + '万'
      }
      return count.toString()
    },
    playGame(game) {
      this.showToast(`${game.name} 游戏功能即将上线`)
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
  background: linear-gradient(90deg, #00d4ff, #7c3aed);
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
  background: linear-gradient(90deg, #00d4ff, #7c3aed);
  border-color: transparent;
  color: #fff;
}

/* Featured Game */
.featured-game {
  position: relative;
  background: linear-gradient(135deg, rgba(0, 212, 255, 0.1) 0%, rgba(124, 58, 237, 0.1) 100%);
  border: 1px solid rgba(0, 212, 255, 0.3);
  border-radius: 15px;
  padding: 20px;
  margin-bottom: 25px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.featured-game:hover {
  transform: translateY(-3px);
  box-shadow: 0 10px 30px rgba(0, 212, 255, 0.2);
}

.featured-badge {
  position: absolute;
  top: -10px;
  left: 15px;
  background: linear-gradient(90deg, #ff6b6b, #ffa502);
  padding: 5px 12px;
  border-radius: 15px;
  font-size: 0.75em;
  font-weight: 600;
}

.featured-content {
  display: flex;
  align-items: center;
  gap: 20px;
  padding-top: 10px;
}

.game-icon-large {
  font-size: 4em;
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 20px;
}

.featured-info {
  flex: 1;
}

.featured-info h3 {
  font-size: 1.2em;
  margin-bottom: 5px;
  color: #fff;
}

.game-desc {
  font-size: 0.85em;
  color: #aaa;
  margin-bottom: 10px;
}

.game-meta {
  display: flex;
  gap: 15px;
  font-size: 0.8em;
  color: #888;
  margin-bottom: 12px;
}

.play-btn {
  background: linear-gradient(90deg, #00d4ff, #7c3aed);
  border: none;
  color: #fff;
  padding: 10px 25px;
  border-radius: 20px;
  font-size: 0.9em;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.play-btn:hover {
  transform: scale(1.05);
  box-shadow: 0 5px 15px rgba(0, 212, 255, 0.3);
}

/* Games Grid */
.games-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.game-card {
  display: flex;
  align-items: center;
  gap: 15px;
  background: rgba(255, 255, 255, 0.05);
  padding: 15px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.game-card:hover {
  background: rgba(255, 255, 255, 0.1);
  transform: translateX(5px);
}

.game-icon {
  font-size: 2.5em;
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 15px;
}

.game-info {
  flex: 1;
}

.game-info h4 {
  font-size: 1em;
  margin-bottom: 3px;
  color: #fff;
}

.game-category {
  font-size: 0.8em;
  color: #888;
  margin-bottom: 5px;
}

.game-stats {
  font-size: 0.75em;
  color: #ffa502;
}

.get-btn {
  background: rgba(0, 212, 255, 0.2);
  border: 1px solid rgba(0, 212, 255, 0.5);
  color: #00d4ff;
  padding: 8px 18px;
  border-radius: 15px;
  font-size: 0.85em;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.get-btn:hover {
  background: #00d4ff;
  color: #fff;
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
  
  .featured-content {
    flex-direction: column;
    text-align: center;
  }
  
  .game-icon-large {
    margin: 0 auto;
  }
  
  .game-meta {
    justify-content: center;
  }
  
  .game-card {
    padding: 12px;
  }
  
  .game-icon {
    width: 50px;
    height: 50px;
    font-size: 2em;
  }
  
  .get-btn {
    padding: 6px 14px;
    font-size: 0.8em;
  }
}
</style>
