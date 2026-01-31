/**
 * 设备适配工具模块
 * 用于检测设备信息并提供适配方案
 */

// 设备信息缓存
let deviceInfo = null

/**
 * 获取设备信息
 * @returns {Object} 设备信息对象
 */
export function getDeviceInfo() {
  if (deviceInfo) return deviceInfo
  
  try {
    const systemInfo = uni.getSystemInfoSync()
    
    deviceInfo = {
      // 基础信息
      platform: systemInfo.platform || 'unknown',
      brand: systemInfo.brand || 'unknown',
      model: systemInfo.model || 'unknown',
      system: systemInfo.system || 'unknown',
      
      // 屏幕信息
      screenWidth: systemInfo.screenWidth || 375,
      screenHeight: systemInfo.screenHeight || 667,
      windowWidth: systemInfo.windowWidth || 375,
      windowHeight: systemInfo.windowHeight || 667,
      pixelRatio: systemInfo.pixelRatio || 2,
      
      // 安全区域
      statusBarHeight: systemInfo.statusBarHeight || 20,
      safeAreaInsets: systemInfo.safeAreaInsets || {
        top: systemInfo.statusBarHeight || 20,
        bottom: 0,
        left: 0,
        right: 0
      },
      safeArea: systemInfo.safeArea || {
        top: systemInfo.statusBarHeight || 20,
        bottom: systemInfo.screenHeight || 667,
        left: 0,
        right: systemInfo.screenWidth || 375,
        width: systemInfo.screenWidth || 375,
        height: (systemInfo.screenHeight || 667) - (systemInfo.statusBarHeight || 20)
      },
      
      // 平台检测
      isIOS: systemInfo.platform === 'ios',
      isAndroid: systemInfo.platform === 'android',
      isH5: false,
      isApp: false,
      isMiniProgram: false,
      
      // 屏幕类型
      isSmallScreen: (systemInfo.screenWidth || 375) < 360,
      isLargeScreen: (systemInfo.screenWidth || 375) >= 414,
      isTablet: (systemInfo.screenWidth || 375) >= 600,
      hasNotch: false,
      
      // 性能相关
      SDKVersion: systemInfo.SDKVersion || '',
      language: systemInfo.language || 'zh-CN',
      version: systemInfo.version || '',
      
      // 原始数据
      raw: systemInfo
    }
    
    // 平台检测
    // #ifdef H5
    deviceInfo.isH5 = true
    // #endif
    
    // #ifdef APP-PLUS
    deviceInfo.isApp = true
    // #endif
    
    // #ifdef MP
    deviceInfo.isMiniProgram = true
    // #endif
    
    // 检测刘海屏 (根据安全区域判断)
    if (deviceInfo.isIOS) {
      // iPhone X 及以上机型底部安全区域大于 0
      const bottomInset = deviceInfo.safeAreaInsets.bottom || 0
      deviceInfo.hasNotch = bottomInset > 0
    } else if (deviceInfo.isAndroid) {
      // Android 刘海屏检测
      const statusBarHeight = deviceInfo.statusBarHeight
      deviceInfo.hasNotch = statusBarHeight > 30
    }
    
    console.log('Device Info:', deviceInfo)
    return deviceInfo
    
  } catch (error) {
    console.error('Get device info failed:', error)
    // 返回默认值
    return {
      platform: 'unknown',
      brand: 'unknown',
      model: 'unknown',
      system: 'unknown',
      screenWidth: 375,
      screenHeight: 667,
      windowWidth: 375,
      windowHeight: 667,
      pixelRatio: 2,
      statusBarHeight: 20,
      safeAreaInsets: { top: 20, bottom: 0, left: 0, right: 0 },
      safeArea: { top: 20, bottom: 667, left: 0, right: 375, width: 375, height: 647 },
      isIOS: false,
      isAndroid: false,
      isH5: true,
      isApp: false,
      isMiniProgram: false,
      isSmallScreen: false,
      isLargeScreen: false,
      isTablet: false,
      hasNotch: false,
      SDKVersion: '',
      language: 'zh-CN',
      version: '',
      raw: {}
    }
  }
}

/**
 * 刷新设备信息
 */
export function refreshDeviceInfo() {
  deviceInfo = null
  return getDeviceInfo()
}

/**
 * 计算视频播放器高度 (根据设备屏幕适配)
 * @param {number} aspectRatio 宽高比 (默认 16:9)
 * @returns {number} 播放器高度 (rpx)
 */
export function calcVideoPlayerHeight(aspectRatio = 16 / 9) {
  const device = getDeviceInfo()
  const screenWidth = device.screenWidth
  
  // 基于屏幕宽度计算高度
  let height = screenWidth / aspectRatio
  
  // 限制最大高度，避免在大屏幕上过高
  const maxHeight = device.screenHeight * 0.4
  if (height > maxHeight) {
    height = maxHeight
  }
  
  // 最小高度限制
  const minHeight = 200
  if (height < minHeight) {
    height = minHeight
  }
  
  // 转换为 rpx (基准 750rpx = 设备宽度)
  const rpxRatio = 750 / device.screenWidth
  return Math.round(height * rpxRatio)
}

/**
 * 获取安全区域内边距
 * @returns {Object} 安全区域内边距 { top, bottom, left, right }
 */
export function getSafeAreaInsets() {
  const device = getDeviceInfo()
  return {
    top: device.safeAreaInsets.top || device.statusBarHeight || 20,
    bottom: device.safeAreaInsets.bottom || 0,
    left: device.safeAreaInsets.left || 0,
    right: device.safeAreaInsets.right || 0
  }
}

/**
 * 获取导航栏总高度 (状态栏 + 导航栏)
 * @returns {number} 导航栏高度 (px)
 */
export function getNavBarHeight() {
  const device = getDeviceInfo()
  const statusBarHeight = device.statusBarHeight || 20
  const navHeight = 44 // 标准导航栏高度
  return statusBarHeight + navHeight
}

/**
 * 获取底部安全区高度
 * @returns {number} 底部安全区高度 (px)
 */
export function getBottomSafeHeight() {
  const device = getDeviceInfo()
  return device.safeAreaInsets.bottom || 0
}

/**
 * 检测是否为低性能设备
 * @returns {boolean}
 */
export function isLowEndDevice() {
  const device = getDeviceInfo()
  
  // 基于像素比和屏幕大小判断
  if (device.pixelRatio < 2) return true
  if (device.screenWidth < 320) return true
  
  // Android 低端设备检测
  if (device.isAndroid) {
    // 检测内存较小的设备 (如果有这个信息)
    const lowEndModels = ['go', 'lite', 'mini', 'neo']
    const modelLower = device.model.toLowerCase()
    for (const keyword of lowEndModels) {
      if (modelLower.includes(keyword)) return true
    }
  }
  
  return false
}

/**
 * 获取网格列数 (根据设备尺寸自适应)
 * @param {number} minWidth 每列最小宽度 (rpx)
 * @returns {number} 列数
 */
export function getGridColumns(minWidth = 320) {
  const device = getDeviceInfo()
  
  // 平板使用更多列
  if (device.isTablet) return 4
  
  // 大屏手机
  if (device.isLargeScreen) return 2
  
  // 小屏手机
  if (device.isSmallScreen) return 1
  
  // 默认 2 列
  return 2
}

/**
 * rpx 转 px
 * @param {number} rpx rpx 值
 * @returns {number} px 值
 */
export function rpxToPx(rpx) {
  const device = getDeviceInfo()
  return Math.round(rpx * device.screenWidth / 750)
}

/**
 * px 转 rpx
 * @param {number} px px 值
 * @returns {number} rpx 值
 */
export function pxToRpx(px) {
  const device = getDeviceInfo()
  return Math.round(px * 750 / device.screenWidth)
}

/**
 * 检测网络状态
 * @returns {Promise<Object>} 网络状态对象
 */
export function getNetworkInfo() {
  return new Promise((resolve) => {
    // #ifdef APP-PLUS || MP
    uni.getNetworkType({
      success: (res) => {
        resolve({
          isConnected: res.networkType !== 'none',
          networkType: res.networkType,
          isWifi: res.networkType === 'wifi',
          is4G: res.networkType === '4g',
          is5G: res.networkType === '5g',
          is2G: res.networkType === '2g',
          is3G: res.networkType === '3g',
          isWeakNetwork: ['2g', '3g'].includes(res.networkType)
        })
      },
      fail: () => {
        resolve({
          isConnected: true,
          networkType: 'unknown',
          isWifi: false,
          is4G: false,
          is5G: false,
          is2G: false,
          is3G: false,
          isWeakNetwork: false
        })
      }
    })
    // #endif
    
    // #ifdef H5
    resolve({
      isConnected: navigator.onLine !== false,
      networkType: 'unknown',
      isWifi: false,
      is4G: false,
      is5G: false,
      is2G: false,
      is3G: false,
      isWeakNetwork: false
    })
    // #endif
  })
}

/**
 * 监听网络状态变化
 * @param {Function} callback 回调函数
 */
export function onNetworkChange(callback) {
  // #ifdef APP-PLUS || MP
  uni.onNetworkStatusChange((res) => {
    callback({
      isConnected: res.isConnected,
      networkType: res.networkType,
      isWifi: res.networkType === 'wifi',
      isWeakNetwork: ['2g', '3g'].includes(res.networkType)
    })
  })
  // #endif
  
  // #ifdef H5
  if (typeof window !== 'undefined') {
    window.addEventListener('online', () => {
      callback({ isConnected: true, networkType: 'unknown' })
    })
    window.addEventListener('offline', () => {
      callback({ isConnected: false, networkType: 'none' })
    })
  }
  // #endif
}

export default {
  getDeviceInfo,
  refreshDeviceInfo,
  calcVideoPlayerHeight,
  getSafeAreaInsets,
  getNavBarHeight,
  getBottomSafeHeight,
  isLowEndDevice,
  getGridColumns,
  rpxToPx,
  pxToRpx,
  getNetworkInfo,
  onNetworkChange
}
