import axios from 'axios'

// Simple in-memory cache for API responses
const cache = new Map()
const CACHE_TTL = 5 * 60 * 1000 // 5 minutes cache TTL

/**
 * Get cached response if valid
 * @param {string} key - Cache key
 * @returns {any|null} - Cached data or null if expired/missing
 */
function getCached(key) {
  const cached = cache.get(key)
  if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
    return cached.data
  }
  cache.delete(key) // Clean up expired entry
  return null
}

/**
 * Set cache entry
 * @param {string} key - Cache key
 * @param {any} data - Data to cache
 */
function setCache(key, data) {
  cache.set(key, { data, timestamp: Date.now() })
}

/**
 * Generate cache key from URL and params
 * @param {string} url - Request URL
 * @param {object} params - Request params
 * @returns {string} - Cache key
 */
function getCacheKey(url, params = {}) {
  return url + '?' + JSON.stringify(params)
}

// Create axios instance with base configuration
const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor with retry configuration
api.interceptors.request.use(
  config => {
    // Add retry count to config for tracking
    config.retryCount = config.retryCount || 0
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// Response interceptor with enhanced error handling
api.interceptors.response.use(
  response => {
    return response.data
  },
  async error => {
    const config = error.config
    
    // Retry logic for network errors (up to 2 retries)
    if (
      config &&
      config.retryCount < 2 &&
      (!error.response || error.response.status >= 500)
    ) {
      config.retryCount += 1
      
      // Exponential backoff: 1s, 2s
      const delay = config.retryCount * 1000
      await new Promise(resolve => setTimeout(resolve, delay))
      
      return api(config)
    }
    
    // Enhanced error logging with more context
    const errorInfo = {
      url: config?.url,
      status: error.response?.status,
      message: error.message,
      retries: config?.retryCount || 0
    }
    console.error('API Error:', errorInfo)
    
    return Promise.reject(error)
  }
)

/**
 * GET request with optional caching
 * @param {string} url - Request URL
 * @param {object} params - Request params
 * @param {boolean} useCache - Whether to use cache (default: true)
 * @returns {Promise} - API response
 */
async function cachedGet(url, params = {}, useCache = true) {
  const cacheKey = getCacheKey(url, params)
  
  if (useCache) {
    const cached = getCached(cacheKey)
    if (cached) {
      return cached
    }
  }
  
  const response = await api.get(url, { params })
  
  if (useCache) {
    setCache(cacheKey, response)
  }
  
  return response
}

// Video API endpoints
export const videoApi = {
  // Get all videos with pagination
  getVideos(params = {}) {
    return cachedGet('/videos', params)
  },

  // Get video by ID
  getVideo(videoId) {
    return cachedGet(`/videos/${videoId}`)
  },

  // Search videos by keyword (no cache - user-initiated searches should be fresh)
  searchVideos(keyword, limit = 20, offset = 0) {
    return api.get('/videos/search', { params: { keyword, limit, offset } })
  },

  // Get videos by category
  getVideosByCategory(category, limit = 20, offset = 0) {
    return cachedGet('/videos/category', { category, limit, offset })
  },

  // Get all categories (cache for longer as categories rarely change)
  getCategories() {
    return cachedGet('/categories')
  },

  // Get top videos by play count
  getTopVideos(limit = 10) {
    return cachedGet('/videos/top', { limit })
  },

  // Update play count (no cache - POST request)
  updatePlayCount(videoId) {
    return api.post(`/videos/${videoId}/play`)
  },

  // Get database statistics
  getStatistics() {
    return cachedGet('/statistics')
  },

  // Clear all cached data (useful for force refresh)
  clearCache() {
    cache.clear()
  }
}

export default api
