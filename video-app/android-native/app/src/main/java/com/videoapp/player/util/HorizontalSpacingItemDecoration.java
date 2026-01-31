package com.videoapp.player.util;

import android.graphics.Rect;
import android.view.View;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

/**
 * Item decoration for horizontal lists with spacing
 */
public class HorizontalSpacingItemDecoration extends RecyclerView.ItemDecoration {

    private final int spacing;
    private final boolean includeEdge;

    public HorizontalSpacingItemDecoration(int spacing, boolean includeEdge) {
        this.spacing = spacing;
        this.includeEdge = includeEdge;
    }

    @Override
    public void getItemOffsets(@NonNull Rect outRect, @NonNull View view,
                               @NonNull RecyclerView parent, @NonNull RecyclerView.State state) {
        int position = parent.getChildAdapterPosition(view);
        int itemCount = state.getItemCount();

        if (includeEdge) {
            if (position == 0) {
                outRect.left = spacing;
            }
            outRect.right = spacing;
        } else {
            if (position < itemCount - 1) {
                outRect.right = spacing;
            }
        }
    }
}
