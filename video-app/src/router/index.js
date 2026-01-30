import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '@/views/HomeView.vue'
import PlayerView from '@/views/PlayerView.vue'

const routes = [
  {
    path: '/',
    name: 'home',
    component: HomeView,
    meta: { title: '视频首页' }
  },
  {
    path: '/player/:id',
    name: 'player',
    component: PlayerView,
    meta: { title: '视频播放' }
  },
  {
    path: '/category/:category',
    name: 'category',
    component: HomeView,
    meta: { title: '分类视频' }
  },
  {
    path: '/search',
    name: 'search',
    component: HomeView,
    meta: { title: '搜索结果' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    // When returning from player to home/category/search, let the component handle scroll restoration
    // This works together with keep-alive's activated/deactivated hooks in HomeView
    if (from.name === 'player' && (to.name === 'home' || to.name === 'category' || to.name === 'search')) {
      // Return undefined to prevent automatic scroll, let HomeView's activated hook handle it
      return
    }
    
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  }
})

router.beforeEach((to, from, next) => {
  document.title = to.meta.title ? `${to.meta.title} - 视频播放器` : '视频播放器'
  next()
})

export default router
