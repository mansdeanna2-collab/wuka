package com.videoapp.player.data.model;

import com.google.gson.annotations.SerializedName;

/**
 * Statistics data model
 */
public class Statistics {

    @SerializedName("total_videos")
    private int totalVideos;

    @SerializedName("total_plays")
    private int totalPlays;

    @SerializedName("total_categories")
    private int totalCategories;

    public int getTotalVideos() {
        return totalVideos;
    }

    public void setTotalVideos(int totalVideos) {
        this.totalVideos = totalVideos;
    }

    public int getTotalPlays() {
        return totalPlays;
    }

    public void setTotalPlays(int totalPlays) {
        this.totalPlays = totalPlays;
    }

    public int getTotalCategories() {
        return totalCategories;
    }

    public void setTotalCategories(int totalCategories) {
        this.totalCategories = totalCategories;
    }
}
