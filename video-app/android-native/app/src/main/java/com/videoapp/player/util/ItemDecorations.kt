package com.videoapp.player.util

import android.graphics.Rect
import android.view.View
import androidx.recyclerview.widget.RecyclerView

/**
 * Item decoration for adding spacing between RecyclerView items
 */
class GridSpacingItemDecoration(
    private val spanCount: Int,
    private val spacing: Int,
    private val includeEdge: Boolean = true
) : RecyclerView.ItemDecoration() {
    
    override fun getItemOffsets(
        outRect: Rect,
        view: View,
        parent: RecyclerView,
        state: RecyclerView.State
    ) {
        val position = parent.getChildAdapterPosition(view)
        val column = position % spanCount
        
        if (includeEdge) {
            outRect.left = spacing - column * spacing / spanCount
            outRect.right = (column + 1) * spacing / spanCount
            
            if (position < spanCount) {
                outRect.top = spacing
            }
            outRect.bottom = spacing
        } else {
            outRect.left = column * spacing / spanCount
            outRect.right = spacing - (column + 1) * spacing / spanCount
            
            if (position >= spanCount) {
                outRect.top = spacing
            }
        }
    }
}

/**
 * Item decoration for horizontal lists with spacing
 */
class HorizontalSpacingItemDecoration(
    private val spacing: Int,
    private val includeEdge: Boolean = true
) : RecyclerView.ItemDecoration() {
    
    override fun getItemOffsets(
        outRect: Rect,
        view: View,
        parent: RecyclerView,
        state: RecyclerView.State
    ) {
        val position = parent.getChildAdapterPosition(view)
        val itemCount = state.itemCount
        
        if (includeEdge) {
            if (position == 0) {
                outRect.left = spacing
            }
            outRect.right = spacing
        } else {
            if (position < itemCount - 1) {
                outRect.right = spacing
            }
        }
    }
}
