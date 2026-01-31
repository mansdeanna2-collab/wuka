package com.videoapp.player.data.model;

import com.google.gson.annotations.SerializedName;

/**
 * Category data model
 */
public class Category {

    @SerializedName("video_category")
    private String videoCategory;

    @SerializedName("video_count")
    private int videoCount;

    public String getVideoCategory() {
        return videoCategory;
    }

    public void setVideoCategory(String videoCategory) {
        this.videoCategory = videoCategory;
    }

    public int getVideoCount() {
        return videoCount;
    }

    public void setVideoCount(int videoCount) {
        this.videoCount = videoCount;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        Category category = (Category) o;
        return videoCategory != null ? videoCategory.equals(category.videoCategory) : category.videoCategory == null;
    }

    @Override
    public int hashCode() {
        return videoCategory != null ? videoCategory.hashCode() : 0;
    }
}
