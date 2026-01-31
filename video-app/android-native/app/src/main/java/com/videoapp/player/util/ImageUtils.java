package com.videoapp.player.util;

import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.util.Base64;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;

import java.net.URLEncoder;
import java.util.HashMap;
import java.util.Map;
import java.util.regex.Pattern;

/**
 * Image utilities for handling various image URL formats
 */
public final class ImageUtils {

    private ImageUtils() {
        // Private constructor to prevent instantiation
    }

    // Base64 image signatures for common image formats
    private static final Map<String, String> BASE64_SIGNATURES = new HashMap<>();
    static {
        BASE64_SIGNATURES.put("/9j/", "image/jpeg");    // JPEG
        BASE64_SIGNATURES.put("iVBOR", "image/png");    // PNG
        BASE64_SIGNATURES.put("R0lGO", "image/gif");    // GIF
        BASE64_SIGNATURES.put("UklGR", "image/webp");   // WebP
        BASE64_SIGNATURES.put("Qk", "image/bmp");       // BMP
    }

    private static final Pattern BASE64_PATTERN = Pattern.compile("^[A-Za-z0-9+/]+={0,2}$");
    private static final Pattern WHITESPACE_PATTERN = Pattern.compile("[\\s\\r\\n]+");

    /**
     * Format image URL - handles base64 content, data URLs, and regular URLs
     */
    @NonNull
    public static String formatImageUrl(@Nullable String url) {
        if (url == null || url.trim().isEmpty()) {
            return "";
        }

        String trimmed = url.trim();

        // If already a data URL, return as-is
        if (trimmed.startsWith("data:")) {
            return trimmed;
        }

        // If a valid URL, return as-is
        if (trimmed.startsWith("http://") || trimmed.startsWith("https://")) {
            return trimmed;
        }

        // Check for known base64 image signatures
        for (Map.Entry<String, String> entry : BASE64_SIGNATURES.entrySet()) {
            if (trimmed.startsWith(entry.getKey())) {
                // Clean base64: remove whitespace
                String cleaned = cleanBase64Content(trimmed);
                if (cleaned != null) {
                    return "data:" + entry.getValue() + ";base64," + cleaned;
                }
            }
        }

        // For other potential base64 content
        String cleanContent = cleanBase64Content(trimmed);
        if (cleanContent != null && cleanContent.length() > 100) {
            // Default to PNG for unknown base64 content
            return "data:image/png;base64," + cleanContent;
        }

        // Otherwise, return as-is
        return trimmed;
    }

    /**
     * Check if URL is a data URL (base64 image)
     */
    public static boolean isDataUrl(@Nullable String url) {
        return url != null && url.startsWith("data:");
    }

    /**
     * Decode base64 image to Bitmap
     */
    @Nullable
    public static Bitmap decodeBase64Image(@NonNull String dataUrl) {
        try {
            // Extract base64 content from data URL
            String base64Data;
            if (dataUrl.contains(",")) {
                base64Data = dataUrl.substring(dataUrl.indexOf(",") + 1);
            } else {
                base64Data = dataUrl;
            }

            byte[] decodedBytes = Base64.decode(base64Data, Base64.DEFAULT);
            return BitmapFactory.decodeByteArray(decodedBytes, 0, decodedBytes.length);
        } catch (Exception e) {
            return null;
        }
    }

    /**
     * Clean and validate base64 content
     */
    @Nullable
    private static String cleanBase64Content(@NonNull String content) {
        // Remove whitespace
        String cleaned = WHITESPACE_PATTERN.matcher(content).replaceAll("");

        // Minimum length check
        if (cleaned.length() < 4) {
            return null;
        }

        // Validate base64 characters and proper padding
        if (!BASE64_PATTERN.matcher(cleaned).matches()) {
            return null;
        }

        // Check length is valid for base64 (must be multiple of 4)
        if (cleaned.length() % 4 != 0) {
            return null;
        }

        return cleaned;
    }

    /**
     * Safe URL encoding
     */
    @NonNull
    public static String safeEncodeUrl(@Nullable String url) {
        if (url == null || url.trim().isEmpty()) {
            return "";
        }
        try {
            return URLEncoder.encode(url, "UTF-8");
        } catch (Exception e) {
            return url;
        }
    }
}
