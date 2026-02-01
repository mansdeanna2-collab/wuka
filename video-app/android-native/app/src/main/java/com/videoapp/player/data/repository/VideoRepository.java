package com.videoapp.player.data.repository;

import android.util.Log;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;

import com.videoapp.player.data.api.ApiClient;
import com.videoapp.player.data.api.VideoApiService;
import com.videoapp.player.data.model.Category;
import com.videoapp.player.data.model.CategoryResponse;
import com.videoapp.player.data.model.SingleVideoResponse;
import com.videoapp.player.data.model.Statistics;
import com.videoapp.player.data.model.StatisticsResponse;
import com.videoapp.player.data.model.Video;
import com.videoapp.player.data.model.VideoResponse;

import java.net.ConnectException;
import java.net.SocketTimeoutException;
import java.net.UnknownHostException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

/**
 * Video repository for managing video data
 */
public class VideoRepository {

    private static final String TAG = "VideoRepository";

    private final VideoApiService apiService;

    public VideoRepository() {
        this.apiService = ApiClient.getInstance().getVideoApiService();
    }

    /**
     * Result callback interface
     */
    public interface ResultCallback<T> {
        void onSuccess(T data);
        void onError(String message);
    }

    /**
     * Convert exception to user-friendly message
     */
    private String getErrorMessage(Throwable e) {
        if (e instanceof UnknownHostException) {
            return "无法连接到服务器，请检查网络";
        } else if (e instanceof SocketTimeoutException) {
            return "连接超时，请稍后重试";
        } else if (e instanceof ConnectException) {
            return "连接被拒绝，请稍后重试";
        } else {
            Log.e(TAG, "API error: " + e.getMessage(), e);
            return e.getMessage() != null ? e.getMessage() : "请求失败";
        }
    }

    /**
     * Get videos with pagination
     */
    public void getVideos(int limit, int offset, @NonNull ResultCallback<List<Video>> callback) {
        apiService.getVideos(limit, offset).enqueue(new Callback<VideoResponse>() {
            @Override
            public void onResponse(@NonNull Call<VideoResponse> call, @NonNull Response<VideoResponse> response) {
                if (response.isSuccessful() && response.body() != null) {
                    List<Video> videos = response.body().getData();
                    callback.onSuccess(videos != null ? videos : Collections.emptyList());
                } else {
                    Log.w(TAG, "getVideos failed with code: " + response.code());
                    callback.onError("服务器错误: " + response.code());
                }
            }

            @Override
            public void onFailure(@NonNull Call<VideoResponse> call, @NonNull Throwable t) {
                callback.onError(getErrorMessage(t));
            }
        });
    }

    /**
     * Get a single video by ID
     */
    public void getVideo(int videoId, @NonNull ResultCallback<Video> callback) {
        apiService.getVideo(videoId).enqueue(new Callback<SingleVideoResponse>() {
            @Override
            public void onResponse(@NonNull Call<SingleVideoResponse> call, @NonNull Response<SingleVideoResponse> response) {
                if (response.isSuccessful() && response.body() != null) {
                    Video video = response.body().getData();
                    if (video != null) {
                        callback.onSuccess(video);
                    } else {
                        callback.onError("视频不存在");
                    }
                } else {
                    Log.w(TAG, "getVideo failed with code: " + response.code());
                    callback.onError("服务器错误: " + response.code());
                }
            }

            @Override
            public void onFailure(@NonNull Call<SingleVideoResponse> call, @NonNull Throwable t) {
                callback.onError(getErrorMessage(t));
            }
        });
    }

    /**
     * Search videos by keyword
     */
    public void searchVideos(String keyword, int limit, int offset, @NonNull ResultCallback<List<Video>> callback) {
        apiService.searchVideos(keyword, limit, offset).enqueue(new Callback<VideoResponse>() {
            @Override
            public void onResponse(@NonNull Call<VideoResponse> call, @NonNull Response<VideoResponse> response) {
                if (response.isSuccessful() && response.body() != null) {
                    List<Video> videos = response.body().getData();
                    callback.onSuccess(videos != null ? videos : Collections.emptyList());
                } else {
                    Log.w(TAG, "searchVideos failed with code: " + response.code());
                    callback.onError("服务器错误: " + response.code());
                }
            }

            @Override
            public void onFailure(@NonNull Call<VideoResponse> call, @NonNull Throwable t) {
                callback.onError(getErrorMessage(t));
            }
        });
    }

    /**
     * Get videos by category
     */
    public void getVideosByCategory(String category, int limit, int offset, @NonNull ResultCallback<List<Video>> callback) {
        apiService.getVideosByCategory(category, limit, offset).enqueue(new Callback<VideoResponse>() {
            @Override
            public void onResponse(@NonNull Call<VideoResponse> call, @NonNull Response<VideoResponse> response) {
                if (response.isSuccessful() && response.body() != null) {
                    List<Video> videos = response.body().getData();
                    callback.onSuccess(videos != null ? videos : Collections.emptyList());
                } else {
                    Log.w(TAG, "getVideosByCategory failed with code: " + response.code());
                    callback.onError("服务器错误: " + response.code());
                }
            }

            @Override
            public void onFailure(@NonNull Call<VideoResponse> call, @NonNull Throwable t) {
                callback.onError(getErrorMessage(t));
            }
        });
    }

    /**
     * Get top videos
     */
    public void getTopVideos(int limit, @NonNull ResultCallback<List<Video>> callback) {
        apiService.getTopVideos(limit).enqueue(new Callback<VideoResponse>() {
            @Override
            public void onResponse(@NonNull Call<VideoResponse> call, @NonNull Response<VideoResponse> response) {
                if (response.isSuccessful() && response.body() != null) {
                    List<Video> videos = response.body().getData();
                    callback.onSuccess(videos != null ? videos : Collections.emptyList());
                } else {
                    Log.w(TAG, "getTopVideos failed with code: " + response.code());
                    callback.onError("服务器错误: " + response.code());
                }
            }

            @Override
            public void onFailure(@NonNull Call<VideoResponse> call, @NonNull Throwable t) {
                callback.onError(getErrorMessage(t));
            }
        });
    }

    /**
     * Update play count for a video
     */
    public void updatePlayCount(int videoId) {
        apiService.updatePlayCount(videoId).enqueue(new Callback<Void>() {
            @Override
            public void onResponse(@NonNull Call<Void> call, @NonNull Response<Void> response) {
                if (!response.isSuccessful()) {
                    Log.d(TAG, "updatePlayCount failed with code: " + response.code());
                }
            }

            @Override
            public void onFailure(@NonNull Call<Void> call, @NonNull Throwable t) {
                // Silently fail for play count updates
                Log.d(TAG, "updatePlayCount failed: " + t.getMessage());
            }
        });
    }

    /**
     * Get all categories
     */
    public void getCategories(@NonNull ResultCallback<List<Category>> callback) {
        apiService.getCategories().enqueue(new Callback<CategoryResponse>() {
            @Override
            public void onResponse(@NonNull Call<CategoryResponse> call, @NonNull Response<CategoryResponse> response) {
                if (response.isSuccessful() && response.body() != null) {
                    List<Category> categories = response.body().getData();
                    callback.onSuccess(categories != null ? categories : Collections.emptyList());
                } else {
                    Log.w(TAG, "getCategories failed with code: " + response.code());
                    callback.onError("服务器错误: " + response.code());
                }
            }

            @Override
            public void onFailure(@NonNull Call<CategoryResponse> call, @NonNull Throwable t) {
                callback.onError(getErrorMessage(t));
            }
        });
    }

    /**
     * Get statistics
     */
    public void getStatistics(@NonNull ResultCallback<Statistics> callback) {
        apiService.getStatistics().enqueue(new Callback<StatisticsResponse>() {
            @Override
            public void onResponse(@NonNull Call<StatisticsResponse> call, @NonNull Response<StatisticsResponse> response) {
                if (response.isSuccessful() && response.body() != null) {
                    Statistics statistics = response.body().getData();
                    if (statistics != null) {
                        callback.onSuccess(statistics);
                    } else {
                        callback.onError("统计信息不可用");
                    }
                } else {
                    Log.w(TAG, "getStatistics failed with code: " + response.code());
                    callback.onError("服务器错误: " + response.code());
                }
            }

            @Override
            public void onFailure(@NonNull Call<StatisticsResponse> call, @NonNull Throwable t) {
                callback.onError(getErrorMessage(t));
            }
        });
    }
}
