package com.videoapp.player.data.model;

import androidx.annotation.Nullable;

import com.google.gson.annotations.SerializedName;

/**
 * API response wrapper for statistics
 */
public class StatisticsResponse {

    @SerializedName("data")
    @Nullable
    private Statistics data;

    @SerializedName("message")
    @Nullable
    private String message;

    @Nullable
    public Statistics getData() {
        return data;
    }

    public void setData(@Nullable Statistics data) {
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
