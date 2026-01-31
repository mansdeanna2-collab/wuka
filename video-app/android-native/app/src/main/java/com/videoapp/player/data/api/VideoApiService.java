package com.videoapp.player.data.api;

import com.videoapp.player.data.model.CategoryResponse;
import com.videoapp.player.data.model.SingleVideoResponse;
import com.videoapp.player.data.model.StatisticsResponse;
import com.videoapp.player.data.model.VideoResponse;

import retrofit2.Call;
import retrofit2.http.GET;
import retrofit2.http.POST;
import retrofit2.http.Path;
import retrofit2.http.Query;

/**
 * Video API interface for Retrofit
 */
public interface VideoApiService {

    /**
     * Get all videos with pagination
     */
    @GET("api/videos")
    Call<VideoResponse> getVideos(
            @Query("limit") int limit,
            @Query("offset") int offset
    );

    /**
     * Get a single video by ID
     */
    @GET("api/videos/{id}")
    Call<SingleVideoResponse> getVideo(
            @Path("id") int videoId
    );

    /**
     * Search videos by keyword
     */
    @GET("api/videos/search")
    Call<VideoResponse> searchVideos(
            @Query("keyword") String keyword,
            @Query("limit") int limit,
            @Query("offset") int offset
    );

    /**
     * Get videos by category
     */
    @GET("api/videos/category")
    Call<VideoResponse> getVideosByCategory(
            @Query("category") String category,
            @Query("limit") int limit,
            @Query("offset") int offset
    );

    /**
     * Get top videos by play count
     */
    @GET("api/videos/top")
    Call<VideoResponse> getTopVideos(
            @Query("limit") int limit
    );

    /**
     * Update play count for a video
     */
    @POST("api/videos/{id}/play")
    Call<Void> updatePlayCount(
            @Path("id") int videoId
    );

    /**
     * Get all categories
     */
    @GET("api/categories")
    Call<CategoryResponse> getCategories();

    /**
     * Get database statistics
     */
    @GET("api/statistics")
    Call<StatisticsResponse> getStatistics();
}
