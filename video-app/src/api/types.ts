/**
 * API Types for Video Application
 * TypeScript interfaces for type-safe API interactions
 */

// Video entity interface
export interface Video {
  video_id: number
  video_url: string
  video_image: string
  video_title: string
  video_category: string
  play_count: number
  upload_time: string
  video_duration: string
  video_coins: number
}

// Category entity interface
export interface Category {
  video_category: string
  count?: number
}

// API response wrapper interface
export interface ApiResponse<T> {
  code: number
  message: string
  data: T
}

// Pagination parameters
export interface PaginationParams {
  limit?: number
  offset?: number
}

// Search parameters
export interface SearchParams extends PaginationParams {
  keyword: string
}

// Category filter parameters
export interface CategoryParams extends PaginationParams {
  category: string
}

// Statistics response
export interface Statistics {
  total_videos: number
  total_categories: number
  total_plays: number
  last_updated?: string
}

// Video list response
export type VideoListResponse = ApiResponse<Video[]>

// Single video response
export type VideoResponse = ApiResponse<Video>

// Category list response
export type CategoryListResponse = ApiResponse<Category[]>

// Statistics response type
export type StatisticsResponse = ApiResponse<Statistics>

// Error response
export interface ApiError {
  code: number
  message: string
  details?: string
}

// Loading states for UI
export interface LoadingState {
  isLoading: boolean
  isRefreshing: boolean
  isLoadingMore: boolean
  error: string | null
}

// Pagination state
export interface PaginationState {
  page: number
  limit: number
  hasMore: boolean
  total?: number
}
