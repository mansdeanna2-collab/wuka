package com.videoapp.player.ui.home;

import android.util.Log;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.lifecycle.LiveData;
import androidx.lifecycle.MutableLiveData;
import androidx.lifecycle.ViewModel;

import com.videoapp.player.data.model.Category;
import com.videoapp.player.data.model.Statistics;
import com.videoapp.player.data.model.Video;
import com.videoapp.player.data.repository.VideoRepository;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * ViewModel for HomeActivity
 */
public class HomeViewModel extends ViewModel {

    private static final String TAG = "HomeViewModel";

    private final VideoRepository repository;

    // Videos list
    private final MutableLiveData<List<Video>> videos = new MutableLiveData<>(Collections.emptyList());

    // Categories list
    private final MutableLiveData<List<Category>> categories = new MutableLiveData<>(Collections.emptyList());

    // Statistics
    private final MutableLiveData<Statistics> statistics = new MutableLiveData<>();

    // Loading state
    private final MutableLiveData<Boolean> isLoading = new MutableLiveData<>(false);

    // Error state
    private final MutableLiveData<String> error = new MutableLiveData<>();

    // Pagination
    private int currentPage = 0;
    private final int pageSize = 20;
    private boolean hasMorePages = true;
    @Nullable
    private String currentCategory = null;
    @Nullable
    private String currentSearchQuery = null;

    // Can load more
    private final MutableLiveData<Boolean> canLoadMore = new MutableLiveData<>(true);

    public HomeViewModel() {
        repository = new VideoRepository();
        loadInitialData();
    }

    @NonNull
    public LiveData<List<Video>> getVideos() {
        return videos;
    }

    @NonNull
    public LiveData<List<Category>> getCategories() {
        return categories;
    }

    @NonNull
    public LiveData<Statistics> getStatistics() {
        return statistics;
    }

    @NonNull
    public LiveData<Boolean> getIsLoading() {
        return isLoading;
    }

    @NonNull
    public LiveData<String> getError() {
        return error;
    }

    @NonNull
    public LiveData<Boolean> getCanLoadMore() {
        return canLoadMore;
    }

    /**
     * Load initial data (videos, categories, statistics)
     */
    public void loadInitialData() {
        isLoading.setValue(true);
        error.setValue(null);

        // Reset pagination state
        currentCategory = null;
        currentSearchQuery = null;
        currentPage = 0;
        hasMorePages = true;
        canLoadMore.setValue(true);

        // Load videos
        repository.getVideos(pageSize, 0, new VideoRepository.ResultCallback<List<Video>>() {
            @Override
            public void onSuccess(List<Video> data) {
                videos.postValue(data);
                hasMorePages = data.size() >= pageSize;
                canLoadMore.postValue(hasMorePages);
                currentPage = 0;
                isLoading.postValue(false);
            }

            @Override
            public void onError(String message) {
                Log.e(TAG, "Failed to load videos: " + message);
                error.postValue(message);
                isLoading.postValue(false);
            }
        });

        // Load categories
        repository.getCategories(new VideoRepository.ResultCallback<List<Category>>() {
            @Override
            public void onSuccess(List<Category> data) {
                categories.postValue(data);
            }

            @Override
            public void onError(String message) {
                Log.d(TAG, "Failed to load categories: " + message);
                // Ignore category errors
            }
        });

        // Load statistics
        repository.getStatistics(new VideoRepository.ResultCallback<Statistics>() {
            @Override
            public void onSuccess(Statistics data) {
                statistics.postValue(data);
            }

            @Override
            public void onError(String message) {
                Log.d(TAG, "Failed to load statistics: " + message);
                // Ignore statistics errors
            }
        });
    }

    /**
     * Refresh data
     */
    public void refresh() {
        currentPage = 0;
        hasMorePages = true;
        canLoadMore.setValue(true);

        if (currentSearchQuery != null) {
            searchVideos(currentSearchQuery);
        } else if (currentCategory != null) {
            loadVideosByCategory(currentCategory);
        } else {
            loadInitialData();
        }
    }

    /**
     * Load more videos (pagination)
     */
    public void loadMore() {
        if (!hasMorePages || Boolean.TRUE.equals(isLoading.getValue())) {
            return;
        }

        isLoading.setValue(true);

        int offset = (currentPage + 1) * pageSize;

        VideoRepository.ResultCallback<List<Video>> callback = new VideoRepository.ResultCallback<List<Video>>() {
            @Override
            public void onSuccess(List<Video> newVideos) {
                List<Video> currentList = videos.getValue();
                List<Video> combined = new ArrayList<>();
                if (currentList != null) {
                    combined.addAll(currentList);
                }
                combined.addAll(newVideos);
                videos.postValue(combined);
                hasMorePages = newVideos.size() >= pageSize;
                canLoadMore.postValue(hasMorePages);
                currentPage++;
                isLoading.postValue(false);
            }

            @Override
            public void onError(String message) {
                Log.e(TAG, "Failed to load more videos: " + message);
                error.postValue(message);
                isLoading.postValue(false);
            }
        };

        if (currentSearchQuery != null) {
            repository.searchVideos(currentSearchQuery, pageSize, offset, callback);
        } else if (currentCategory != null) {
            repository.getVideosByCategory(currentCategory, pageSize, offset, callback);
        } else {
            repository.getVideos(pageSize, offset, callback);
        }
    }

    /**
     * Search videos by keyword
     */
    public void searchVideos(@NonNull String query) {
        String trimmedQuery = query.trim();
        currentSearchQuery = trimmedQuery.isEmpty() ? null : trimmedQuery;
        currentCategory = null;
        currentPage = 0;
        hasMorePages = true;
        canLoadMore.setValue(true);

        if (currentSearchQuery == null) {
            loadInitialData();
            return;
        }

        isLoading.setValue(true);
        error.setValue(null);

        repository.searchVideos(currentSearchQuery, pageSize, 0, new VideoRepository.ResultCallback<List<Video>>() {
            @Override
            public void onSuccess(List<Video> data) {
                videos.postValue(data);
                hasMorePages = data.size() >= pageSize;
                canLoadMore.postValue(hasMorePages);
                isLoading.postValue(false);
            }

            @Override
            public void onError(String message) {
                Log.e(TAG, "Search failed: " + message);
                error.postValue(message);
                videos.postValue(Collections.emptyList());
                isLoading.postValue(false);
            }
        });
    }

    /**
     * Load videos by category
     */
    public void loadVideosByCategory(@Nullable String category) {
        currentCategory = category;
        currentSearchQuery = null;
        currentPage = 0;
        hasMorePages = true;
        canLoadMore.setValue(true);

        if (category == null) {
            loadInitialData();
            return;
        }

        isLoading.setValue(true);
        error.setValue(null);

        repository.getVideosByCategory(category, pageSize, 0, new VideoRepository.ResultCallback<List<Video>>() {
            @Override
            public void onSuccess(List<Video> data) {
                videos.postValue(data);
                hasMorePages = data.size() >= pageSize;
                canLoadMore.postValue(hasMorePages);
                isLoading.postValue(false);
            }

            @Override
            public void onError(String message) {
                Log.e(TAG, "Failed to load category: " + message);
                error.postValue(message);
                videos.postValue(Collections.emptyList());
                isLoading.postValue(false);
            }
        });
    }

    /**
     * Clear error message
     */
    public void clearError() {
        error.setValue(null);
    }
}
