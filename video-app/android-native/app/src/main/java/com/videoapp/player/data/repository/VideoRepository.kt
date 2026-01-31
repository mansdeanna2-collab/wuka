package com.videoapp.player.data.repository

import com.videoapp.player.data.api.ApiClient
import com.videoapp.player.data.model.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

/**
 * Video repository for managing video data
 */
class VideoRepository {
    
    private val apiService = ApiClient.videoApiService
    
    /**
     * Get videos with pagination
     */
    suspend fun getVideos(limit: Int = 20, offset: Int = 0): Result<List<Video>> {
        return withContext(Dispatchers.IO) {
            try {
                val response = apiService.getVideos(limit, offset)
                if (response.isSuccessful) {
                    val videos = response.body()?.data ?: emptyList()
                    Result.success(videos)
                } else {
                    Result.failure(Exception("API Error: ${response.code()}"))
                }
            } catch (e: Exception) {
                Result.failure(e)
            }
        }
    }
    
    /**
     * Get a single video by ID
     */
    suspend fun getVideo(videoId: Int): Result<Video> {
        return withContext(Dispatchers.IO) {
            try {
                val response = apiService.getVideo(videoId)
                if (response.isSuccessful) {
                    response.body()?.data?.let {
                        Result.success(it)
                    } ?: Result.failure(Exception("Video not found"))
                } else {
                    Result.failure(Exception("API Error: ${response.code()}"))
                }
            } catch (e: Exception) {
                Result.failure(e)
            }
        }
    }
    
    /**
     * Search videos by keyword
     */
    suspend fun searchVideos(keyword: String, limit: Int = 20, offset: Int = 0): Result<List<Video>> {
        return withContext(Dispatchers.IO) {
            try {
                val response = apiService.searchVideos(keyword, limit, offset)
                if (response.isSuccessful) {
                    val videos = response.body()?.data ?: emptyList()
                    Result.success(videos)
                } else {
                    Result.failure(Exception("API Error: ${response.code()}"))
                }
            } catch (e: Exception) {
                Result.failure(e)
            }
        }
    }
    
    /**
     * Get videos by category
     */
    suspend fun getVideosByCategory(category: String, limit: Int = 20, offset: Int = 0): Result<List<Video>> {
        return withContext(Dispatchers.IO) {
            try {
                val response = apiService.getVideosByCategory(category, limit, offset)
                if (response.isSuccessful) {
                    val videos = response.body()?.data ?: emptyList()
                    Result.success(videos)
                } else {
                    Result.failure(Exception("API Error: ${response.code()}"))
                }
            } catch (e: Exception) {
                Result.failure(e)
            }
        }
    }
    
    /**
     * Get top videos
     */
    suspend fun getTopVideos(limit: Int = 10): Result<List<Video>> {
        return withContext(Dispatchers.IO) {
            try {
                val response = apiService.getTopVideos(limit)
                if (response.isSuccessful) {
                    val videos = response.body()?.data ?: emptyList()
                    Result.success(videos)
                } else {
                    Result.failure(Exception("API Error: ${response.code()}"))
                }
            } catch (e: Exception) {
                Result.failure(e)
            }
        }
    }
    
    /**
     * Update play count for a video
     */
    suspend fun updatePlayCount(videoId: Int): Result<Unit> {
        return withContext(Dispatchers.IO) {
            try {
                val response = apiService.updatePlayCount(videoId)
                if (response.isSuccessful) {
                    Result.success(Unit)
                } else {
                    Result.failure(Exception("API Error: ${response.code()}"))
                }
            } catch (e: Exception) {
                Result.failure(e)
            }
        }
    }
    
    /**
     * Get all categories
     */
    suspend fun getCategories(): Result<List<Category>> {
        return withContext(Dispatchers.IO) {
            try {
                val response = apiService.getCategories()
                if (response.isSuccessful) {
                    val categories = response.body()?.data ?: emptyList()
                    Result.success(categories)
                } else {
                    Result.failure(Exception("API Error: ${response.code()}"))
                }
            } catch (e: Exception) {
                Result.failure(e)
            }
        }
    }
    
    /**
     * Get statistics
     */
    suspend fun getStatistics(): Result<Statistics> {
        return withContext(Dispatchers.IO) {
            try {
                val response = apiService.getStatistics()
                if (response.isSuccessful) {
                    response.body()?.data?.let {
                        Result.success(it)
                    } ?: Result.failure(Exception("Statistics not available"))
                } else {
                    Result.failure(Exception("API Error: ${response.code()}"))
                }
            } catch (e: Exception) {
                Result.failure(e)
            }
        }
    }
}
