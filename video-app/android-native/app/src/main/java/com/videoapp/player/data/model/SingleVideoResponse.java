package com.videoapp.player.data.model;

import androidx.annotation.Nullable;

import com.google.gson.annotations.SerializedName;

/**
 * API response wrapper for single video
 */
public class SingleVideoResponse {

    @SerializedName("data")
    @Nullable
    private Video data;

    @SerializedName("message")
    @Nullable
    private String message;

    @Nullable
    public Video getData() {
        return data;
    }

    public void setData(@Nullable Video data) {
        this.data = data;
    }

    @Nullable
    public String getMessage() {
        return message;
    }

    public void setMessage(@Nullable String message) {
        this.message = message;
    }
}
