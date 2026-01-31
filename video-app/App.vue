<template>
  <view class="app">
    <!-- uni-app pages are managed by pages.json for all platforms including H5 -->
  </view>
</template>

<script>
import { API_CONFIG, APP_CONFIG } from '@/config'

export default {
  name: 'App',
  
  globalData: {
    // API 基础地址
    apiBaseUrl: API_CONFIG.current.baseUrl,
    
    // 应用版本
    version: APP_CONFIG.version,
    
    // 用户信息
    userInfo: null,
    
    // 系统信息
    systemInfo: null,
    
    // 设备信息
    deviceInfo: null,
    
    // 状态栏高度
    statusBarHeight: 0,
    
    // 导航栏高度
    navBarHeight: 44,
    
    // 安全区域
    safeAreaInsets: {
      top: 20,
      bottom: 0,
      left: 0,
      right: 0
    },
    
    // 是否刘海屏
    hasNotch: false,
    
    // 网络状态
    networkInfo: {
      isConnected: true,
      networkType: 'unknown',
      isWeakNetwork: false
    },
    
    // 是否已初始化
    isInitialized: false
  },
  
  onLaunch() {
    console.log('App Launch - Version:', APP_CONFIG.version)
    
    // 初始化应用
    this.initApp()
  },
  
  onShow() {
    console.log('App Show')
    // 检查网络状态
    this.checkNetworkStatus()
  },
  
  onHide() {
    console.log('App Hide')
  },
  
  onError(error) {
    console.error('App Error:', error)
    // 可以在这里上报错误日志
  },
  
  methods: {
    /**
     * 初始化应用
     */
    async initApp() {
      try {
        // 获取系统信息
        await this.getSystemInfo()
        
        // 设置状态栏样式
        this.setStatusBarStyle()
        
        // 初始化网络监听
        this.initNetworkListener()
        
        // 检查更新
        this.checkUpdate()
        
        // 标记初始化完成
        this.globalData.isInitialized = true
        
        console.log('App initialized successfully', {
          platform: this.globalData.systemInfo?.platform,
          model: this.globalData.systemInfo?.model,
          hasNotch: this.globalData.hasNotch
        })
      } catch (error) {
        console.error('App initialization failed:', error)
      }
    },
    
    /**
     * 获取系统信息
     */
    getSystemInfo() {
      return new Promise((resolve) => {
        try {
          const systemInfo = uni.getSystemInfoSync()
          this.globalData.systemInfo = systemInfo
          this.globalData.statusBarHeight = systemInfo.statusBarHeight || 20
          
          // 设置安全区域
          if (systemInfo.safeAreaInsets) {
            this.globalData.safeAreaInsets = systemInfo.safeAreaInsets
          } else if (systemInfo.safeArea) {
            this.globalData.safeAreaInsets = {
              top: systemInfo.safeArea.top || systemInfo.statusBarHeight || 20,
              bottom: systemInfo.screenHeight - (systemInfo.safeArea.bottom || systemInfo.screenHeight),
              left: systemInfo.safeArea.left || 0,
              right: systemInfo.screenWidth - (systemInfo.safeArea.right || systemInfo.screenWidth)
            }
          }
          
          // 检测刘海屏
          if (systemInfo.platform === 'ios') {
            this.globalData.hasNotch = (this.globalData.safeAreaInsets.bottom || 0) > 0
          } else if (systemInfo.platform === 'android') {
            this.globalData.hasNotch = (systemInfo.statusBarHeight || 0) > 30
          }
          
          // #ifdef MP-WEIXIN
          // 微信小程序获取胶囊按钮位置
          const menuButtonInfo = uni.getMenuButtonBoundingClientRect()
          this.globalData.navBarHeight = menuButtonInfo.bottom + menuButtonInfo.top - systemInfo.statusBarHeight
          // #endif
          
          console.log('System info:', {
            platform: systemInfo.platform,
            model: systemInfo.model,
            screenWidth: systemInfo.screenWidth,
            screenHeight: systemInfo.screenHeight,
            statusBarHeight: systemInfo.statusBarHeight,
            hasNotch: this.globalData.hasNotch
          })
          
          resolve(systemInfo)
        } catch (error) {
          console.error('Get system info failed:', error)
          resolve(null)
        }
      })
    },
    
    /**
     * 初始化网络状态监听
     */
    initNetworkListener() {
      // #ifdef APP-PLUS || MP
      uni.getNetworkType({
        success: (res) => {
          this.globalData.networkInfo = {
            isConnected: res.networkType !== 'none',
            networkType: res.networkType,
            isWeakNetwork: ['2g', '3g'].includes(res.networkType)
          }
        }
      })
      
      uni.onNetworkStatusChange((res) => {
        this.globalData.networkInfo = {
          isConnected: res.isConnected,
          networkType: res.networkType,
          isWeakNetwork: ['2g', '3g'].includes(res.networkType)
        }
        
        if (!res.isConnected) {
          uni.showToast({
            title: '网络连接已断开',
            icon: 'none',
            duration: 2000
          })
        }
      })
      // #endif
    },
    
    /**
     * 检查网络状态
     */
    checkNetworkStatus() {
      // #ifdef APP-PLUS || MP
      uni.getNetworkType({
        success: (res) => {
          this.globalData.networkInfo.isConnected = res.networkType !== 'none'
          this.globalData.networkInfo.networkType = res.networkType
        }
      })
      // #endif
    },
    
    /**
     * 设置状态栏样式
     */
    setStatusBarStyle() {
      // #ifdef APP-PLUS
      try {
        plus.navigator.setStatusBarStyle('light')
        plus.navigator.setStatusBarBackground('#1a1a2e')
      } catch (e) {
        console.warn('Set status bar style failed:', e)
      }
      // #endif
    },
    
    /**
     * 检查应用更新
     */
    checkUpdate() {
      // #ifdef APP-PLUS
      // App 端可以在这里检查热更新
      // #endif
      
      // #ifdef MP-WEIXIN
      // 微信小程序检查更新
      if (uni.canIUse('getUpdateManager')) {
        const updateManager = uni.getUpdateManager()
        
        updateManager.onCheckForUpdate((res) => {
          if (res.hasUpdate) {
            console.log('发现新版本')
          }
        })
        
        updateManager.onUpdateReady(() => {
          uni.showModal({
            title: '更新提示',
            content: '新版本已经准备好，是否重启应用？',
            success: (res) => {
              if (res.confirm) {
                updateManager.applyUpdate()
              }
            }
          })
        })
        
        updateManager.onUpdateFailed(() => {
          console.error('新版本下载失败')
        })
      }
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
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans SC', sans-serif;
  font-size: 28rpx;
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* 盒模型 */
view, text, image, button, input, textarea, scroll-view {
  box-sizing: border-box;
}

/* #ifndef H5 */
/* 非 H5 平台隐藏滚动条 */
::-webkit-scrollbar {
  display: none;
  width: 0;
  height: 0;
  color: transparent;
}
/* #endif */

/* 重置按钮样式 */
button {
  margin: 0;
  padding: 0;
  background: transparent;
  border: none;
  line-height: inherit;
  font-size: inherit;
  color: inherit;
}

button::after {
  border: none;
}

/* 输入框样式 */
input {
  box-sizing: border-box;
}

input::placeholder {
  color: #666;
}

/* 图片默认样式 */
image {
  display: block;
  max-width: 100%;
}

/* 文本溢出省略 */
.text-ellipsis {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.text-ellipsis-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.text-ellipsis-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Flex 布局助手 */
.flex {
  display: flex;
}

.flex-row {
  display: flex;
  flex-direction: row;
}

.flex-col {
  display: flex;
  flex-direction: column;
}

.flex-wrap {
  flex-wrap: wrap;
}

.flex-1 {
  flex: 1;
}

.items-center {
  align-items: center;
}

.justify-center {
  justify-content: center;
}

.justify-between {
  justify-content: space-between;
}

.justify-around {
  justify-content: space-around;
}

/* 安全区域适配 */
.safe-area-bottom {
  padding-bottom: constant(safe-area-inset-bottom);
  padding-bottom: env(safe-area-inset-bottom);
}

.safe-area-top {
  padding-top: constant(safe-area-inset-top);
  padding-top: env(safe-area-inset-top);
}

/* 滚动条样式 (H5) */
/* #ifdef H5 */
::-webkit-scrollbar {
  display: block;
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
/* #endif */
</style>
