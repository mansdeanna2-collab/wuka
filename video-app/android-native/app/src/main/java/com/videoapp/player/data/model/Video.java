package com.videoapp.player.data.model;

import androidx.annotation.Nullable;

import com.google.gson.annotations.SerializedName;

/**
 * Video data model matching the API response
 */
public class Video {

    @SerializedName("video_id")
    private int videoId;

    @SerializedName("video_title")
    private String videoTitle;

    @SerializedName("video_url")
    private String videoUrl;

    @SerializedName("video_image")
    @Nullable
    private String videoImage;

    @SerializedName("video_category")
    @Nullable
    private String videoCategory;

    @SerializedName("video_duration")
    @Nullable
    private String videoDuration;

    @SerializedName("video_coins")
    @Nullable
    private Integer videoCoins;

    @SerializedName("play_count")
    @Nullable
    private Integer playCount;

    @SerializedName("upload_time")
    @Nullable
    private String uploadTime;

    public int getVideoId() {
        return videoId;
    }

    public void setVideoId(int videoId) {
        this.videoId = videoId;
    }

    public String getVideoTitle() {
        return videoTitle;
    }

    public void setVideoTitle(String videoTitle) {
        this.videoTitle = videoTitle;
    }

    public String getVideoUrl() {
        return videoUrl;
    }

    public void setVideoUrl(String videoUrl) {
        this.videoUrl = videoUrl;
    }

    @Nullable
    public String getVideoImage() {
        return videoImage;
    }

    public void setVideoImage(@Nullable String videoImage) {
        this.videoImage = videoImage;
    }

    @Nullable
    public String getVideoCategory() {
        return videoCategory;
    }

    public void setVideoCategory(@Nullable String videoCategory) {
        this.videoCategory = videoCategory;
    }

    @Nullable
    public String getVideoDuration() {
        return videoDuration;
    }

    public void setVideoDuration(@Nullable String videoDuration) {
        this.videoDuration = videoDuration;
    }

    @Nullable
    public Integer getVideoCoins() {
        return videoCoins;
    }

    public void setVideoCoins(@Nullable Integer videoCoins) {
        this.videoCoins = videoCoins;
    }

    @Nullable
    public Integer getPlayCount() {
        return playCount;
    }

    public void setPlayCount(@Nullable Integer playCount) {
        this.playCount = playCount;
    }

    @Nullable
    public String getUploadTime() {
        return uploadTime;
    }

    public void setUploadTime(@Nullable String uploadTime) {
        this.uploadTime = uploadTime;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        Video video = (Video) o;
        return videoId == video.videoId;
    }

    @Override
    public int hashCode() {
        return Integer.hashCode(videoId);
    }
}
