<template>
  <view class="app">
    <!-- #ifdef H5 -->
    <router-view></router-view>
    <!-- #endif -->
    <!-- #ifndef H5 -->
    <!-- uni-app pages are managed by pages.json -->
    <!-- #endif -->
  </view>
</template>

<script>
export default {
  name: 'App',
  onLaunch() {
    console.log('App Launch')
    // #ifdef APP-PLUS
    // App 端初始化
    this.initApp()
    // #endif
  },
  onShow() {
    console.log('App Show')
  },
  onHide() {
    console.log('App Hide')
  },
  methods: {
    initApp() {
      // 设置状态栏样式
      // #ifdef APP-PLUS
      plus.navigator.setStatusBarStyle('light')
      // #endif
    }
  }
}
</script>

<style>
/* 全局样式 */
page {
  background-color: #0a0a1a;
  color: #ffffff;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

view, text {
  box-sizing: border-box;
}

/* 重置按钮样式 */
button {
  margin: 0;
  padding: 0;
  background: transparent;
  border: none;
  line-height: inherit;
}

button::after {
  border: none;
}

/* 输入框样式 */
input {
  box-sizing: border-box;
}

/* 图片默认样式 */
image {
  display: block;
}

/* 滚动条样式 (H5) */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.3);
}
</style>
