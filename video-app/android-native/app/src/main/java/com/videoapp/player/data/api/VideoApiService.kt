package com.videoapp.player.data.api

import com.videoapp.player.data.model.*
import retrofit2.Response
import retrofit2.http.*

/**
 * Video API interface for Retrofit
 */
interface VideoApiService {
    
    /**
     * Get all videos with pagination
     */
    @GET("api/videos")
    suspend fun getVideos(
        @Query("limit") limit: Int = 20,
        @Query("offset") offset: Int = 0
    ): Response<VideoResponse>
    
    /**
     * Get a single video by ID
     */
    @GET("api/videos/{id}")
    suspend fun getVideo(
        @Path("id") videoId: Int
    ): Response<SingleVideoResponse>
    
    /**
     * Search videos by keyword
     */
    @GET("api/videos/search")
    suspend fun searchVideos(
        @Query("keyword") keyword: String,
        @Query("limit") limit: Int = 20,
        @Query("offset") offset: Int = 0
    ): Response<VideoResponse>
    
    /**
     * Get videos by category
     */
    @GET("api/videos/category")
    suspend fun getVideosByCategory(
        @Query("category") category: String,
        @Query("limit") limit: Int = 20,
        @Query("offset") offset: Int = 0
    ): Response<VideoResponse>
    
    /**
     * Get top videos by play count
     */
    @GET("api/videos/top")
    suspend fun getTopVideos(
        @Query("limit") limit: Int = 10
    ): Response<VideoResponse>
    
    /**
     * Update play count for a video
     */
    @POST("api/videos/{id}/play")
    suspend fun updatePlayCount(
        @Path("id") videoId: Int
    ): Response<Unit>
    
    /**
     * Get all categories
     */
    @GET("api/categories")
    suspend fun getCategories(): Response<CategoryResponse>
    
    /**
     * Get database statistics
     */
    @GET("api/statistics")
    suspend fun getStatistics(): Response<StatisticsResponse>
}
