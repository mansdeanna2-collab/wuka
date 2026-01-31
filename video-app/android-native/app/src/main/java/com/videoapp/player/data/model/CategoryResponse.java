package com.videoapp.player.data.model;

import androidx.annotation.Nullable;

import com.google.gson.annotations.SerializedName;

import java.util.List;

/**
 * API response wrapper for categories
 */
public class CategoryResponse {

    @SerializedName("data")
    @Nullable
    private List<Category> data;

    @SerializedName("message")
    @Nullable
    private String message;

    @Nullable
    public List<Category> getData() {
        return data;
    }

    public void setData(@Nullable List<Category> data) {
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
