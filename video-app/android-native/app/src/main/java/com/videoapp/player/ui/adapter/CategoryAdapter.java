package com.videoapp.player.ui.adapter;

import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.recyclerview.widget.DiffUtil;
import androidx.recyclerview.widget.ListAdapter;
import androidx.recyclerview.widget.RecyclerView;

import com.videoapp.player.R;
import com.videoapp.player.data.model.Category;
import com.videoapp.player.databinding.ItemCategoryChipBinding;

/**
 * Adapter for displaying categories as chips
 */
public class CategoryAdapter extends ListAdapter<Category, CategoryAdapter.CategoryViewHolder> {

    private static final String TAG = "CategoryAdapter";

    public interface OnCategoryClickListener {
        void onCategoryClick(@Nullable Category category);
    }

    private final OnCategoryClickListener onCategoryClick;
    private int selectedPosition = 0;
    private final boolean showAllOption = true;

    public CategoryAdapter(@NonNull OnCategoryClickListener onCategoryClick) {
        super(new CategoryDiffCallback());
        this.onCategoryClick = onCategoryClick;
    }

    @NonNull
    @Override
    public CategoryViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        ItemCategoryChipBinding binding = ItemCategoryChipBinding.inflate(
                LayoutInflater.from(parent.getContext()),
                parent,
                false
        );
        return new CategoryViewHolder(binding);
    }

    @Override
    public void onBindViewHolder(@NonNull CategoryViewHolder holder, int position) {
        try {
            if (showAllOption && position == 0) {
                holder.bindAllOption(position == selectedPosition);
            } else {
                int adjustedPosition = showAllOption ? position - 1 : position;
                int itemCount = super.getItemCount();

                // Bounds check to prevent IndexOutOfBoundsException
                if (adjustedPosition >= 0 && adjustedPosition < itemCount) {
                    holder.bind(getItem(adjustedPosition), position == selectedPosition);
                } else {
                    // Fallback to "All" option if position is out of bounds
                    Log.w(TAG, "Position " + adjustedPosition + " out of bounds (count: " + itemCount + "), showing fallback");
                    holder.bindAllOption(false);
                }
            }
        } catch (Exception e) {
            Log.e(TAG, "Error binding category at position " + position, e);
            // Safe fallback
            holder.bindAllOption(false);
        }
    }

    @Override
    public int getItemCount() {
        return super.getItemCount() + (showAllOption ? 1 : 0);
    }

    public void selectCategory(int position) {
        try {
            int oldPosition = selectedPosition;
            selectedPosition = position;

            // Validate positions before notifying
            int totalCount = getItemCount();
            if (oldPosition >= 0 && oldPosition < totalCount) {
                notifyItemChanged(oldPosition);
            }
            if (position >= 0 && position < totalCount) {
                notifyItemChanged(position);
            }
        } catch (Exception e) {
            Log.e(TAG, "Error selecting category at position " + position, e);
        }
    }

    class CategoryViewHolder extends RecyclerView.ViewHolder {

        private final ItemCategoryChipBinding binding;

        CategoryViewHolder(@NonNull ItemCategoryChipBinding binding) {
            super(binding.getRoot());
            this.binding = binding;

            binding.getRoot().setOnClickListener(v -> {
                try {
                    int position = getBindingAdapterPosition();
                    if (position != RecyclerView.NO_POSITION) {
                        selectCategory(position);
                        if (showAllOption && position == 0) {
                            onCategoryClick.onCategoryClick(null);
                        } else {
                            int adjustedPosition = showAllOption ? position - 1 : position;
                            int itemCount = getCurrentList().size();

                            if (adjustedPosition >= 0 && adjustedPosition < itemCount) {
                                onCategoryClick.onCategoryClick(getItem(adjustedPosition));
                            } else {
                                // If out of bounds, treat as "All" category
                                onCategoryClick.onCategoryClick(null);
                            }
                        }
                    }
                } catch (Exception e) {
                    Log.e(TAG, "Error handling category click", e);
                    // Fallback to "All" on error
                    onCategoryClick.onCategoryClick(null);
                }
            });
        }

        void bind(@NonNull Category category, boolean isSelected) {
            binding.categoryName.setText(category.getVideoCategory());
            binding.categoryCount.setText("(" + category.getVideoCount() + ")");
            binding.categoryCount.setVisibility(View.VISIBLE);

            updateSelection(isSelected);
        }

        void bindAllOption(boolean isSelected) {
            binding.categoryName.setText(itemView.getContext().getString(R.string.all_categories));
            binding.categoryCount.setVisibility(View.GONE);

            updateSelection(isSelected);
        }

        private void updateSelection(boolean isSelected) {
            binding.getRoot().setSelected(isSelected);
            binding.getRoot().setAlpha(isSelected ? 1.0f : 0.7f);
        }
    }

    /**
     * DiffUtil callback for efficient list updates
     */
    static class CategoryDiffCallback extends DiffUtil.ItemCallback<Category> {
        @Override
        public boolean areItemsTheSame(@NonNull Category oldItem, @NonNull Category newItem) {
            String oldCategory = oldItem.getVideoCategory();
            String newCategory = newItem.getVideoCategory();
            return oldCategory != null ? oldCategory.equals(newCategory) : newCategory == null;
        }

        @Override
        public boolean areContentsTheSame(@NonNull Category oldItem, @NonNull Category newItem) {
            return oldItem.equals(newItem);
        }
    }
}
