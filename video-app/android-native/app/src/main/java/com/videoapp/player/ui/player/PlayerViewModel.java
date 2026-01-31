package com.videoapp.player.ui.player;

import android.util.Log;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.lifecycle.LiveData;
import androidx.lifecycle.MutableLiveData;
import androidx.lifecycle.ViewModel;

import com.videoapp.player.data.model.Video;
import com.videoapp.player.data.repository.VideoRepository;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * ViewModel for PlayerActivity
 */
public class PlayerViewModel extends ViewModel {

    private static final String TAG = "PlayerViewModel";

    private final VideoRepository repository;

    // Current video
    private final MutableLiveData<Video> video = new MutableLiveData<>();

    // Related videos
    private final MutableLiveData<List<Video>> relatedVideos = new MutableLiveData<>(Collections.emptyList());

    // Loading state
    private final MutableLiveData<Boolean> isLoading = new MutableLiveData<>(false);

    // Error state
    private final MutableLiveData<String> error = new MutableLiveData<>();

    // Current video ID
    private int currentVideoId = 0;

    public PlayerViewModel() {
        repository = new VideoRepository();
    }

    @NonNull
    public LiveData<Video> getVideo() {
        return video;
    }

    @NonNull
    public LiveData<List<Video>> getRelatedVideos() {
        return relatedVideos;
    }

    @NonNull
    public LiveData<Boolean> getIsLoading() {
        return isLoading;
    }

    @NonNull
    public LiveData<String> getError() {
        return error;
    }

    /**
     * Load video by ID
     */
    public void loadVideo(int videoId) {
        if (videoId == currentVideoId && video.getValue() != null) {
            return;
        }

        currentVideoId = videoId;

        isLoading.setValue(true);
        error.setValue(null);

        repository.getVideo(videoId, new VideoRepository.ResultCallback<Video>() {
            @Override
            public void onSuccess(Video data) {
                video.postValue(data);
                // Load related videos
                loadRelatedVideos(data);
                isLoading.postValue(false);
            }

            @Override
            public void onError(String message) {
                Log.e(TAG, "Failed to load video " + videoId + ": " + message);
                error.postValue(message);
                isLoading.postValue(false);
            }
        });
    }

    /**
     * Load related videos based on category
     */
    private void loadRelatedVideos(@NonNull Video currentVideo) {
        String category = currentVideo.getVideoCategory();
        if (category == null || category.isEmpty()) {
            relatedVideos.postValue(Collections.emptyList());
            return;
        }

        repository.getVideosByCategory(category, 6, 0, new VideoRepository.ResultCallback<List<Video>>() {
            @Override
            public void onSuccess(List<Video> videos) {
                // Filter out current video
                List<Video> filtered = new ArrayList<>();
                for (Video v : videos) {
                    if (v.getVideoId() != currentVideo.getVideoId()) {
                        filtered.add(v);
                    }
                }
                relatedVideos.postValue(filtered);
            }

            @Override
            public void onError(String message) {
                Log.d(TAG, "Failed to load related videos: " + message);
                relatedVideos.postValue(Collections.emptyList());
            }
        });
    }

    /**
     * Update play count when video starts playing
     */
    public void updatePlayCount(int videoId) {
        repository.updatePlayCount(videoId);
    }

    /**
     * Clear error message
     */
    public void clearError() {
        error.setValue(null);
    }

    /**
     * Get parsed video URLs for multi-episode content
     * Format: name1$url1#name2$url2
     */
    @NonNull
    public List<Episode> getEpisodes() {
        Video currentVideo = video.getValue();
        if (currentVideo == null) {
            return Collections.emptyList();
        }

        String url = currentVideo.getVideoUrl();
        if (url == null || url.trim().isEmpty()) {
            return Collections.emptyList();
        }

        List<Episode> episodes = new ArrayList<>();

        try {
            if (url.contains("#")) {
                String[] parts = url.split("#");
                for (int index = 0; index < parts.length; index++) {
                    String part = parts[index];
                    if (part.trim().isEmpty()) {
                        continue;
                    }
                    if (part.contains("$")) {
                        String[] subParts = part.split("\\$", 2);
                        if (subParts.length == 2 && !subParts[1].trim().isEmpty()) {
                            episodes.add(new Episode(subParts[0], subParts[1]));
                        } else if (subParts.length > 0 && !subParts[0].trim().isEmpty()) {
                            episodes.add(new Episode("第" + (index + 1) + "集", subParts[0]));
                        }
                    } else {
                        episodes.add(new Episode("第" + (index + 1) + "集", part));
                    }
                }
            } else if (url.contains("$")) {
                String[] parts = url.split("\\$", 2);
                if (parts.length == 2 && !parts[1].trim().isEmpty()) {
                    episodes.add(new Episode(parts[0], parts[1]));
                } else if (parts.length > 0 && !parts[0].trim().isEmpty()) {
                    episodes.add(new Episode("", parts[0]));
                }
            } else {
                episodes.add(new Episode("", url));
            }
        } catch (Exception e) {
            Log.e(TAG, "Error parsing episodes", e);
            // Fallback: treat the entire URL as a single episode
            if (!url.trim().isEmpty()) {
                episodes.add(new Episode("", url));
            }
        }

        return episodes;
    }

    /**
     * Episode data class
     */
    public static class Episode {
        private final String name;
        private final String url;

        public Episode(@NonNull String name, @NonNull String url) {
            this.name = name;
            this.url = url;
        }

        @NonNull
        public String getName() {
            return name;
        }

        @NonNull
        public String getUrl() {
            return url;
        }
    }
}
