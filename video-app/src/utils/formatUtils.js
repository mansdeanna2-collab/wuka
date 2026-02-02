/**
 * Format utilities for consistent display formatting across the app
 */

/**
 * Format play count with Chinese number formatting
 * @param {number} count - The play count to format
 * @returns {string} - Formatted play count string
 */
export function formatPlayCount(count) {
  if (!count || count <= 0 || !isFinite(count)) return '0'
  if (count >= 100000000) {
    return (count / 100000000).toFixed(1) + '亿'
  }
  if (count >= 10000) {
    return (count / 10000).toFixed(1) + '万'
  }
  return count.toString()
}

/**
 * Format duration from seconds to HH:MM:SS or MM:SS
 * @param {number} seconds - Duration in seconds
 * @returns {string} - Formatted duration string
 */
export function formatDuration(seconds) {
  if (!seconds || seconds <= 0 || !isFinite(seconds)) return '00:00'
  
  const hrs = Math.floor(seconds / 3600)
  const mins = Math.floor((seconds % 3600) / 60)
  const secs = Math.floor(seconds % 60)
  
  if (hrs > 0) {
    return `${hrs}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

/**
 * Format relative time (e.g., "2 hours ago", "3 days ago")
 * Note: Uses approximate day counts (30 days/month, 365 days/year) for simplicity
 * @param {string|Date} dateInput - Date string or Date object
 * @returns {string} - Relative time string in Chinese, empty string for invalid/future dates
 */
export function formatRelativeTime(dateInput) {
  if (!dateInput) return ''
  
  const date = typeof dateInput === 'string' ? new Date(dateInput) : dateInput
  if (isNaN(date.getTime())) return ''
  
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  
  // Handle future dates - return empty string
  if (diffMs < 0) return ''
  
  const diffSeconds = Math.floor(diffMs / 1000)
  const diffMinutes = Math.floor(diffSeconds / 60)
  const diffHours = Math.floor(diffMinutes / 60)
  const diffDays = Math.floor(diffHours / 24)
  // Using approximate values: 30 days/month, 365 days/year
  const diffMonths = Math.floor(diffDays / 30)
  const diffYears = Math.floor(diffDays / 365)
  
  if (diffSeconds < 60) return '刚刚'
  if (diffMinutes < 60) return `${diffMinutes}分钟前`
  if (diffHours < 24) return `${diffHours}小时前`
  if (diffDays < 30) return `${diffDays}天前`
  if (diffMonths < 12) return `${diffMonths}个月前`
  return `${diffYears}年前`
}

/**
 * Format file size
 * @param {number} bytes - Size in bytes
 * @returns {string} - Formatted size string
 */
export function formatFileSize(bytes) {
  if (!bytes || bytes <= 0) return '0 B'
  
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let unitIndex = 0
  let size = bytes
  
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex++
  }
  
  return `${size.toFixed(unitIndex > 0 ? 1 : 0)} ${units[unitIndex]}`
}

/**
 * Validate video URL format
 * Checks if the URL is a valid video source URL
 * @param {string} url - The video URL to validate
 * @returns {boolean} - True if valid, false otherwise
 */
export function isValidVideoUrl(url) {
  if (!url || typeof url !== 'string') return false
  
  const trimmed = url.trim()
  if (!trimmed) return false
  
  // Check for common video URL patterns
  // 1. HTTP/HTTPS URLs (most common)
  if (trimmed.startsWith('http://') || trimmed.startsWith('https://')) {
    // Check for common video extensions or streaming patterns
    const videoPatterns = [
      /\.mp4(\?|$)/i,
      /\.m3u8(\?|$)/i,
      /\.webm(\?|$)/i,
      /\.mov(\?|$)/i,
      /\.flv(\?|$)/i,
      /\.avi(\?|$)/i,
      /\.mkv(\?|$)/i,
      /\/play\//i,
      /\/video\//i,
      /\/stream\//i,
      /\/hls\//i
    ]
    
    // If any pattern matches, it's likely a video URL
    if (videoPatterns.some(pattern => pattern.test(trimmed))) {
      return true
    }
    
    // For URLs without obvious extensions, still consider them valid
    // as many streaming services use dynamic URLs
    return true
  }
  
  // 2. Episode format: name$url or name$url#name2$url2
  if (trimmed.includes('$') || trimmed.includes('#')) {
    const parts = trimmed.split('#')
    return parts.every(part => {
      // All parts in episode format must contain '$'
      if (!part.includes('$')) {
        return false
      }
      const urlPart = part.split('$')[1]
      return urlPart && (urlPart.startsWith('http://') || urlPart.startsWith('https://'))
    })
  }
  
  return false
}

/**
 * Extract the main video URL from various formats
 * Handles episode format: name$url#name2$url2
 * @param {string} src - The video source string
 * @returns {string} - The extracted video URL or empty string
 */
export function extractVideoUrl(src) {
  if (!src || typeof src !== 'string') return ''
  
  const trimmed = src.trim()
  if (!trimmed) return ''
  
  // If already a valid URL, return it
  if (trimmed.startsWith('http://') || trimmed.startsWith('https://')) {
    return trimmed
  }
  
  // Handle episode format: name$url
  if (trimmed.includes('$')) {
    const firstPart = trimmed.split('#')[0]
    const parts = firstPart.split('$')
    if (parts.length >= 2 && parts[1]) {
      return parts[1].trim()
    }
  }
  
  return ''
}

/**
 * Get video format/type from URL
 * @param {string} url - The video URL
 * @returns {string} - Video type (e.g., 'mp4', 'm3u8', 'unknown')
 */
export function getVideoFormat(url) {
  if (!url || typeof url !== 'string') return 'unknown'
  
  const trimmed = url.trim().toLowerCase()
  
  if (trimmed.includes('.m3u8')) return 'm3u8'
  if (trimmed.includes('.mp4')) return 'mp4'
  if (trimmed.includes('.webm')) return 'webm'
  if (trimmed.includes('.mov')) return 'mov'
  if (trimmed.includes('.flv')) return 'flv'
  if (trimmed.includes('.avi')) return 'avi'
  if (trimmed.includes('.mkv')) return 'mkv'
  
  return 'unknown'
}

export default {
  formatPlayCount,
  formatDuration,
  formatRelativeTime,
  formatFileSize,
  isValidVideoUrl,
  extractVideoUrl,
  getVideoFormat
}
