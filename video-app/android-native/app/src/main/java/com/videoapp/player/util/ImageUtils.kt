package com.videoapp.player.util

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.util.Base64
import java.net.URLEncoder

/**
 * Image utilities for handling various image URL formats
 */
object ImageUtils {
    
    // Base64 image signatures for common image formats
    private val BASE64_SIGNATURES = mapOf(
        "/9j/" to "image/jpeg",    // JPEG
        "iVBOR" to "image/png",    // PNG
        "R0lGO" to "image/gif",    // GIF
        "UklGR" to "image/webp",   // WebP
        "Qk" to "image/bmp"        // BMP
    )
    
    /**
     * Format image URL - handles base64 content, data URLs, and regular URLs
     */
    fun formatImageUrl(url: String?): String {
        if (url.isNullOrBlank()) return ""
        
        val trimmed = url.trim()
        
        // If already a data URL, return as-is
        if (trimmed.startsWith("data:")) {
            return trimmed
        }
        
        // If a valid URL, return as-is
        if (trimmed.startsWith("http://") || trimmed.startsWith("https://")) {
            return trimmed
        }
        
        // Check for known base64 image signatures
        for ((signature, mimeType) in BASE64_SIGNATURES) {
            if (trimmed.startsWith(signature)) {
                // Clean base64: remove whitespace
                val cleaned = cleanBase64Content(trimmed)
                if (cleaned != null) {
                    return "data:$mimeType;base64,$cleaned"
                }
            }
        }
        
        // For other potential base64 content
        val cleanContent = cleanBase64Content(trimmed)
        if (cleanContent != null && cleanContent.length > 100) {
            // Default to PNG for unknown base64 content
            return "data:image/png;base64,$cleanContent"
        }
        
        // Otherwise, return as-is
        return trimmed
    }
    
    /**
     * Check if URL is a data URL (base64 image)
     */
    fun isDataUrl(url: String?): Boolean {
        return url?.startsWith("data:") == true
    }
    
    /**
     * Decode base64 image to Bitmap
     */
    fun decodeBase64Image(dataUrl: String): Bitmap? {
        return try {
            // Extract base64 content from data URL
            val base64Data = if (dataUrl.contains(",")) {
                dataUrl.substringAfter(",")
            } else {
                dataUrl
            }
            
            val decodedBytes = Base64.decode(base64Data, Base64.DEFAULT)
            BitmapFactory.decodeByteArray(decodedBytes, 0, decodedBytes.size)
        } catch (e: Exception) {
            null
        }
    }
    
    /**
     * Clean and validate base64 content
     */
    private fun cleanBase64Content(content: String): String? {
        // Remove whitespace
        val cleaned = content.replace(Regex("[\\s\\r\\n]+"), "")
        
        // Minimum length check
        if (cleaned.length < 4) {
            return null
        }
        
        // Validate base64 characters and proper padding
        if (!Regex("^[A-Za-z0-9+/]+={0,2}$").matches(cleaned)) {
            return null
        }
        
        // Check length is valid for base64 (must be multiple of 4)
        if (cleaned.length % 4 != 0) {
            return null
        }
        
        return cleaned
    }
    
    /**
     * Safe URL encoding
     */
    fun safeEncodeUrl(url: String?): String {
        if (url.isNullOrBlank()) return ""
        return try {
            URLEncoder.encode(url, "UTF-8")
        } catch (e: Exception) {
            url
        }
    }
}
