package com.videoapp.player.data.model;

import androidx.annotation.Nullable;

import com.google.gson.annotations.SerializedName;

import java.util.List;

/**
 * API response wrapper for videos
 */
public class VideoResponse {

    @SerializedName("data")
    @Nullable
    private List<Video> data;

    @SerializedName("total")
    @Nullable
    private Integer total;

    @SerializedName("message")
    @Nullable
    private String message;

    @Nullable
    public List<Video> getData() {
        return data;
    }

    public void setData(@Nullable List<Video> data) {
        this.data = data;
    }

    @Nullable
    public Integer getTotal() {
        return total;
    }

    public void setTotal(@Nullable Integer total) {
        this.total = total;
    }

    @Nullable
    public String getMessage() {
        return message;
    }

    public void setMessage(@Nullable String message) {
        this.message = message;
    }
}
