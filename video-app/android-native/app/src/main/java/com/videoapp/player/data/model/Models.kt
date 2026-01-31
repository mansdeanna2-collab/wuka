package com.videoapp.player.data.model

import com.google.gson.annotations.SerializedName

/**
 * Video data model matching the API response
 */
data class Video(
    @SerializedName("video_id")
    val videoId: Int,
    
    @SerializedName("video_title")
    val videoTitle: String,
    
    @SerializedName("video_url")
    val videoUrl: String,
    
    @SerializedName("video_image")
    val videoImage: String?,
    
    @SerializedName("video_category")
    val videoCategory: String?,
    
    @SerializedName("video_duration")
    val videoDuration: String?,
    
    @SerializedName("video_coins")
    val videoCoins: Int?,
    
    @SerializedName("play_count")
    val playCount: Int?,
    
    @SerializedName("upload_time")
    val uploadTime: String?
)

/**
 * Category data model
 */
data class Category(
    @SerializedName("video_category")
    val videoCategory: String,
    
    @SerializedName("video_count")
    val videoCount: Int
)

/**
 * Statistics data model
 */
data class Statistics(
    @SerializedName("total_videos")
    val totalVideos: Int,
    
    @SerializedName("total_plays")
    val totalPlays: Int,
    
    @SerializedName("total_categories")
    val totalCategories: Int
)

/**
 * API response wrapper for videos
 */
data class VideoResponse(
    @SerializedName("data")
    val data: List<Video>?,
    
    @SerializedName("total")
    val total: Int?,
    
    @SerializedName("message")
    val message: String?
)

/**
 * API response wrapper for single video
 */
data class SingleVideoResponse(
    @SerializedName("data")
    val data: Video?,
    
    @SerializedName("message")
    val message: String?
)

/**
 * API response wrapper for categories
 */
data class CategoryResponse(
    @SerializedName("data")
    val data: List<Category>?,
    
    @SerializedName("message")
    val message: String?
)

/**
 * API response wrapper for statistics
 */
data class StatisticsResponse(
    @SerializedName("data")
    val data: Statistics?,
    
    @SerializedName("message")
    val message: String?
)
