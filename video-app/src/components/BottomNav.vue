<template>
  <nav class="bottom-nav" aria-label="Bottom navigation / 底部导航">
    <ul class="nav-items">
      <li v-for="item in navItems" :key="item.path" class="nav-item-wrapper">
        <router-link 
          :to="item.path"
          class="nav-item"
          :class="{ active: isActive(item.path) }"
        >
          <AppIcon class="nav-icon" :name="item.icon" :size="24" />
          <span class="nav-label">{{ item.label }}</span>
        </router-link>
      </li>
    </ul>
  </nav>
</template>

<script>
import AppIcon from '@/components/AppIcon.vue'

export default {
  name: 'BottomNav',
  components: { AppIcon },
  data() {
    return {
      navItems: [
        { path: '/', icon: 'home', label: '首页' },
        { path: '/darkweb', icon: 'globe', label: '暗网' },
        { path: '/live', icon: 'tv', label: '直播' },
        { path: '/games', icon: 'gamepad', label: '游戏' },
        { path: '/profile', icon: 'user', label: '我的' }
      ]
    }
  },
  methods: {
    isActive(path) {
      if (path === '/') {
        return this.$route.path === '/' || 
               this.$route.path.startsWith('/category') ||
               this.$route.path.startsWith('/search')
      }
      return this.$route.path.startsWith(path)
    }
  }
}
</script>

<style scoped>
.bottom-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: rgba(26, 26, 46, 0.98);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  padding: 8px 0;
  padding-bottom: calc(8px + env(safe-area-inset-bottom));
  z-index: 1000;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.nav-items {
  display: flex;
  justify-content: space-around;
  align-items: center;
  width: 100%;
  list-style: none;
  padding: 0;
  margin: 0;
}

.nav-item-wrapper {
  flex: 1;
  display: flex;
  justify-content: center;
}

.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 5px 15px;
  color: #8a8aa0;
  text-decoration: none;
  transition: color 0.25s ease, transform 0.25s ease;
  min-width: 60px;
}

.nav-item.active {
  color: #00d4ff;
}

.nav-item:hover {
  color: #00d4ff;
}

.nav-item:active {
  transform: scale(0.94);
}

.nav-icon {
  transition: transform 0.25s ease;
}

.nav-item.active .nav-icon {
  transform: translateY(-1px) scale(1.08);
  filter: drop-shadow(0 2px 8px rgba(0, 212, 255, 0.45));
}

.nav-label {
  font-size: 0.7em;
  font-weight: 500;
  letter-spacing: 0.02em;
}

/* Mobile responsive */
@media (max-width: 480px) {
  .nav-item {
    padding: 4px 10px;
    min-width: 50px;
  }
  
  .nav-icon {
    width: 22px;
    height: 22px;
  }
  
  .nav-label {
    font-size: 0.65em;
  }
}

/* Large screens - keep bottom nav visible */
@media (min-width: 768px) {
  .bottom-nav {
    display: block;
  }
}
</style>
