package com.videoapp.player.ui.home;

import android.content.Intent;
import android.os.Bundle;
import android.text.Editable;
import android.text.TextWatcher;
import android.util.Log;
import android.view.Menu;
import android.view.View;
import android.view.inputmethod.EditorInfo;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import androidx.lifecycle.ViewModelProvider;
import androidx.recyclerview.widget.GridLayoutManager;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import com.videoapp.player.R;
import com.videoapp.player.data.model.Category;
import com.videoapp.player.data.model.Statistics;
import com.videoapp.player.data.model.Video;
import com.videoapp.player.databinding.ActivityHomeBinding;
import com.videoapp.player.ui.adapter.CategoryAdapter;
import com.videoapp.player.ui.adapter.VideoAdapter;
import com.videoapp.player.ui.player.PlayerActivity;
import com.videoapp.player.util.GridSpacingItemDecoration;
import com.videoapp.player.util.HorizontalSpacingItemDecoration;
import com.videoapp.player.util.KeyboardUtils;
import com.videoapp.player.util.NetworkUtils;

import java.util.List;

/**
 * Home Activity - displays video grid with search and category filtering
 */
public class HomeActivity extends AppCompatActivity {

    private static final String TAG = "HomeActivity";
    private static final int ITEM_SPACING_DP = 8;

    @Nullable
    private ActivityHomeBinding binding;

    private HomeViewModel viewModel;

    @Nullable
    private VideoAdapter videoAdapter;
    @Nullable
    private CategoryAdapter categoryAdapter;

    private int itemSpacingPx = 16;

    @Override
    protected void onCreate(@Nullable Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        try {
            binding = ActivityHomeBinding.inflate(getLayoutInflater());
            setContentView(binding.getRoot());

            // Calculate item spacing
            itemSpacingPx = (int) (ITEM_SPACING_DP * getResources().getDisplayMetrics().density);

            viewModel = new ViewModelProvider(this).get(HomeViewModel.class);

            setupToolbar();
            setupVideoRecyclerView();
            setupCategoryRecyclerView();
            setupSearchView();
            setupSwipeRefresh();
            observeViewModel();
        } catch (Exception e) {
            Log.e(TAG, "Error in onCreate", e);
            Toast.makeText(this, "初始化失败，请重启应用", Toast.LENGTH_LONG).show();
        }
    }

    private void setupToolbar() {
        try {
            if (binding != null) {
                setSupportActionBar(binding.toolbar);
                if (getSupportActionBar() != null) {
                    getSupportActionBar().setDisplayShowTitleEnabled(false);
                }
            }
        } catch (Exception e) {
            Log.e(TAG, "Error setting up toolbar", e);
        }
    }

    @Override
    public boolean onCreateOptionsMenu(Menu menu) {
        try {
            getMenuInflater().inflate(R.menu.menu_home, menu);
        } catch (Exception e) {
            Log.e(TAG, "Error inflating menu", e);
        }
        return true;
    }

    private void setupVideoRecyclerView() {
        if (binding == null) return;

        try {
            videoAdapter = new VideoAdapter(this::navigateToPlayer);

            // Calculate span count based on screen width
            int spanCount = calculateSpanCount();

            binding.videoRecyclerView.setLayoutManager(new GridLayoutManager(this, spanCount));
            binding.videoRecyclerView.setAdapter(videoAdapter);

            // Add spacing decoration
            binding.videoRecyclerView.addItemDecoration(new GridSpacingItemDecoration(spanCount, itemSpacingPx, true));

            // Enable item animator for smooth updates
            RecyclerView.ItemAnimator animator = binding.videoRecyclerView.getItemAnimator();
            if (animator != null) {
                animator.setChangeDuration(150);
            }

            // Optimize for fixed size items
            binding.videoRecyclerView.setHasFixedSize(true);

            // Infinite scroll
            binding.videoRecyclerView.addOnScrollListener(new RecyclerView.OnScrollListener() {
                @Override
                public void onScrolled(@NonNull RecyclerView recyclerView, int dx, int dy) {
                    super.onScrolled(recyclerView, dx, dy);

                    try {
                        // Only load more when scrolling down
                        if (dy <= 0) return;

                        RecyclerView.LayoutManager layoutManager = recyclerView.getLayoutManager();
                        if (!(layoutManager instanceof GridLayoutManager)) return;

                        GridLayoutManager gridLayoutManager = (GridLayoutManager) layoutManager;

                        int visibleItemCount = gridLayoutManager.getChildCount();
                        int totalItemCount = gridLayoutManager.getItemCount();
                        int firstVisibleItemPosition = gridLayoutManager.findFirstVisibleItemPosition();

                        Boolean canLoadMoreValue = viewModel.getCanLoadMore().getValue();
                        Boolean isLoadingValue = viewModel.getIsLoading().getValue();

                        if (Boolean.TRUE.equals(canLoadMoreValue) &&
                                !Boolean.TRUE.equals(isLoadingValue) &&
                                (visibleItemCount + firstVisibleItemPosition) >= totalItemCount - 4) {
                            viewModel.loadMore();
                        }
                    } catch (Exception e) {
                        Log.e(TAG, "Error in scroll listener", e);
                    }
                }
            });
        } catch (Exception e) {
            Log.e(TAG, "Error setting up video RecyclerView", e);
        }
    }

    private int calculateSpanCount() {
        try {
            float screenWidthDp = getResources().getDisplayMetrics().widthPixels / getResources().getDisplayMetrics().density;
            if (screenWidthDp >= 600) {
                return 3;  // Tablet
            } else if (screenWidthDp >= 480) {
                return 2;  // Large phone
            } else {
                return 2;  // Normal phone
            }
        } catch (Exception e) {
            Log.e(TAG, "Error calculating span count", e);
            return 2; // Default fallback
        }
    }

    private void setupCategoryRecyclerView() {
        if (binding == null) return;

        try {
            categoryAdapter = new CategoryAdapter(category -> {
                String categoryName = category != null ? category.getVideoCategory() : null;
                viewModel.loadVideosByCategory(categoryName);
            });

            binding.categoryRecyclerView.setLayoutManager(
                    new LinearLayoutManager(this, LinearLayoutManager.HORIZONTAL, false)
            );
            binding.categoryRecyclerView.setAdapter(categoryAdapter);

            // Add horizontal spacing
            binding.categoryRecyclerView.addItemDecoration(new HorizontalSpacingItemDecoration(itemSpacingPx, false));

            // Optimize for fixed size items
            binding.categoryRecyclerView.setHasFixedSize(true);
        } catch (Exception e) {
            Log.e(TAG, "Error setting up category RecyclerView", e);
        }
    }

    private void setupSearchView() {
        if (binding == null) return;

        try {
            binding.searchEditText.setOnEditorActionListener((v, actionId, event) -> {
                if (actionId == EditorInfo.IME_ACTION_SEARCH) {
                    performSearch();
                    return true;
                }
                return false;
            });

            binding.searchEditText.addTextChangedListener(new TextWatcher() {
                @Override
                public void beforeTextChanged(CharSequence s, int start, int count, int after) {
                }

                @Override
                public void onTextChanged(CharSequence s, int start, int before, int count) {
                }

                @Override
                public void afterTextChanged(Editable s) {
                    if (binding != null) {
                        binding.clearSearchButton.setVisibility(
                                s == null || s.length() == 0 ? View.GONE : View.VISIBLE
                        );
                    }
                }
            });

            binding.searchButton.setOnClickListener(v -> performSearch());

            binding.clearSearchButton.setOnClickListener(v -> {
                if (binding != null) {
                    binding.searchEditText.getText().clear();
                    viewModel.loadInitialData();
                }
            });

            // Retry button in empty view
            binding.retryButton.setOnClickListener(v -> viewModel.refresh());
        } catch (Exception e) {
            Log.e(TAG, "Error setting up search view", e);
        }
    }

    private void performSearch() {
        if (binding == null) return;

        try {
            Editable text = binding.searchEditText.getText();
            String query = text != null ? text.toString().trim() : "";
            if (!query.isEmpty()) {
                // Check network connectivity
                if (!NetworkUtils.isNetworkAvailable(this)) {
                    Toast.makeText(this, NetworkUtils.getNetworkErrorMessage(this), Toast.LENGTH_SHORT).show();
                    return;
                }

                viewModel.searchVideos(query);
                // Hide keyboard
                KeyboardUtils.hideKeyboard(this);
                binding.searchEditText.clearFocus();
            }
        } catch (Exception e) {
            Log.e(TAG, "Error performing search", e);
        }
    }

    private void setupSwipeRefresh() {
        if (binding == null) return;

        try {
            binding.swipeRefreshLayout.setOnRefreshListener(() -> viewModel.refresh());

            // Set colors
            binding.swipeRefreshLayout.setColorSchemeResources(
                    R.color.colorPrimary,
                    R.color.colorAccent
            );
        } catch (Exception e) {
            Log.e(TAG, "Error setting up swipe refresh", e);
        }
    }

    private void observeViewModel() {
        try {
            // Observe videos
            viewModel.getVideos().observe(this, videos -> {
                try {
                    if (videoAdapter != null) {
                        videoAdapter.submitList(videos);
                    }
                    Boolean isLoadingValue = viewModel.getIsLoading().getValue();
                    updateEmptyView(videos.isEmpty() && !Boolean.TRUE.equals(isLoadingValue));
                } catch (Exception e) {
                    Log.e(TAG, "Error updating videos", e);
                }
            });

            // Observe categories
            viewModel.getCategories().observe(this, categories -> {
                try {
                    if (categoryAdapter != null) {
                        categoryAdapter.submitList(categories);
                    }
                } catch (Exception e) {
                    Log.e(TAG, "Error updating categories", e);
                }
            });

            // Observe statistics
            viewModel.getStatistics().observe(this, statistics -> {
                try {
                    if (binding != null) {
                        if (statistics != null) {
                            binding.statsText.setText(getString(
                                    R.string.stats_format,
                                    statistics.getTotalVideos(),
                                    statistics.getTotalPlays()
                            ));
                            binding.statsText.setVisibility(View.VISIBLE);
                        } else {
                            binding.statsText.setVisibility(View.GONE);
                        }
                    }
                } catch (Exception e) {
                    Log.e(TAG, "Error updating statistics", e);
                }
            });

            // Observe loading state
            viewModel.getIsLoading().observe(this, isLoading -> {
                try {
                    if (binding != null) {
                        binding.swipeRefreshLayout.setRefreshing(Boolean.TRUE.equals(isLoading));

                        // Show loading indicator for initial load
                        int adapterItemCount = videoAdapter != null ? videoAdapter.getItemCount() : 0;
                        binding.loadingView.setVisibility(
                                Boolean.TRUE.equals(isLoading) && adapterItemCount == 0 ? View.VISIBLE : View.GONE
                        );

                        // Update empty view when loading completes
                        if (!Boolean.TRUE.equals(isLoading)) {
                            updateEmptyView(adapterItemCount == 0);
                        }
                    }
                } catch (Exception e) {
                    Log.e(TAG, "Error updating loading state", e);
                }
            });

            // Observe errors
            viewModel.getError().observe(this, errorMsg -> {
                try {
                    if (errorMsg != null) {
                        Toast.makeText(this, errorMsg, Toast.LENGTH_SHORT).show();
                        // Show retry button when there's an error
                        int adapterItemCount = videoAdapter != null ? videoAdapter.getItemCount() : 0;
                        if (adapterItemCount == 0) {
                            showErrorState(errorMsg);
                        }
                        viewModel.clearError();
                    }
                } catch (Exception e) {
                    Log.e(TAG, "Error handling error state", e);
                }
            });
        } catch (Exception e) {
            Log.e(TAG, "Error setting up observers", e);
        }
    }

    private void updateEmptyView(boolean isEmpty) {
        if (binding == null) return;

        try {
            binding.emptyView.setVisibility(isEmpty ? View.VISIBLE : View.GONE);
            if (isEmpty) {
                binding.emptyIcon.setText("📭");
                binding.emptyText.setText(getString(R.string.no_videos));
                binding.retryButton.setVisibility(View.GONE);
            }
        } catch (Exception e) {
            Log.e(TAG, "Error updating empty view", e);
        }
    }

    private void showErrorState(@NonNull String error) {
        if (binding == null) return;

        try {
            binding.emptyView.setVisibility(View.VISIBLE);
            binding.emptyIcon.setText("⚠️");
            binding.emptyText.setText(error);
            binding.retryButton.setVisibility(View.VISIBLE);
        } catch (Exception e) {
            Log.e(TAG, "Error showing error state", e);
        }
    }

    private void navigateToPlayer(@NonNull Video video) {
        try {
            Intent intent = new Intent(this, PlayerActivity.class);
            intent.putExtra(PlayerActivity.EXTRA_VIDEO_ID, video.getVideoId());
            startActivity(intent);
        } catch (Exception e) {
            Log.e(TAG, "Error navigating to player", e);
            Toast.makeText(this, "无法打开视频", Toast.LENGTH_SHORT).show();
        }
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        // Clean up binding to prevent memory leaks
        binding = null;
        videoAdapter = null;
        categoryAdapter = null;
    }
}
