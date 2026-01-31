package com.videoapp.player.ui.home

import android.content.Intent
import android.os.Bundle
import android.view.Menu
import android.view.View
import android.view.inputmethod.EditorInfo
import android.widget.Toast
import androidx.activity.viewModels
import androidx.appcompat.app.AppCompatActivity
import androidx.core.widget.addTextChangedListener
import androidx.recyclerview.widget.GridLayoutManager
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.videoapp.player.R
import com.videoapp.player.data.model.Video
import com.videoapp.player.databinding.ActivityHomeBinding
import com.videoapp.player.ui.adapter.CategoryAdapter
import com.videoapp.player.ui.adapter.VideoAdapter
import com.videoapp.player.ui.player.PlayerActivity

/**
 * Home Activity - displays video grid with search and category filtering
 */
class HomeActivity : AppCompatActivity() {
    
    private lateinit var binding: ActivityHomeBinding
    private val viewModel: HomeViewModel by viewModels()
    
    private lateinit var videoAdapter: VideoAdapter
    private lateinit var categoryAdapter: CategoryAdapter
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityHomeBinding.inflate(layoutInflater)
        setContentView(binding.root)
        
        setupToolbar()
        setupVideoRecyclerView()
        setupCategoryRecyclerView()
        setupSearchView()
        setupSwipeRefresh()
        observeViewModel()
    }
    
    private fun setupToolbar() {
        setSupportActionBar(binding.toolbar)
        supportActionBar?.setDisplayShowTitleEnabled(false)
    }
    
    override fun onCreateOptionsMenu(menu: Menu): Boolean {
        menuInflater.inflate(R.menu.menu_home, menu)
        return true
    }
    
    private fun setupVideoRecyclerView() {
        videoAdapter = VideoAdapter { video ->
            navigateToPlayer(video)
        }
        
        // Calculate span count based on screen width
        val spanCount = calculateSpanCount()
        
        binding.videoRecyclerView.apply {
            layoutManager = GridLayoutManager(this@HomeActivity, spanCount)
            adapter = videoAdapter
            
            // Infinite scroll
            addOnScrollListener(object : RecyclerView.OnScrollListener() {
                override fun onScrolled(recyclerView: RecyclerView, dx: Int, dy: Int) {
                    super.onScrolled(recyclerView, dx, dy)
                    
                    val layoutManager = recyclerView.layoutManager as GridLayoutManager
                    val visibleItemCount = layoutManager.childCount
                    val totalItemCount = layoutManager.itemCount
                    val firstVisibleItemPosition = layoutManager.findFirstVisibleItemPosition()
                    
                    if (viewModel.canLoadMore.value == true &&
                        viewModel.isLoading.value != true &&
                        (visibleItemCount + firstVisibleItemPosition) >= totalItemCount - 4
                    ) {
                        viewModel.loadMore()
                    }
                }
            })
        }
    }
    
    private fun calculateSpanCount(): Int {
        val displayMetrics = resources.displayMetrics
        val screenWidthDp = displayMetrics.widthPixels / displayMetrics.density
        return when {
            screenWidthDp >= 600 -> 3  // Tablet
            screenWidthDp >= 480 -> 2  // Large phone
            else -> 2                  // Normal phone
        }
    }
    
    private fun setupCategoryRecyclerView() {
        categoryAdapter = CategoryAdapter { category ->
            viewModel.loadVideosByCategory(category?.videoCategory)
        }
        
        binding.categoryRecyclerView.apply {
            layoutManager = LinearLayoutManager(
                this@HomeActivity,
                LinearLayoutManager.HORIZONTAL,
                false
            )
            adapter = categoryAdapter
        }
    }
    
    private fun setupSearchView() {
        binding.searchEditText.apply {
            setOnEditorActionListener { _, actionId, _ ->
                if (actionId == EditorInfo.IME_ACTION_SEARCH) {
                    performSearch()
                    true
                } else {
                    false
                }
            }
            
            addTextChangedListener { text ->
                binding.clearSearchButton.visibility = 
                    if (text.isNullOrEmpty()) View.GONE else View.VISIBLE
            }
        }
        
        binding.searchButton.setOnClickListener {
            performSearch()
        }
        
        binding.clearSearchButton.setOnClickListener {
            binding.searchEditText.text.clear()
            viewModel.loadInitialData()
        }
    }
    
    private fun performSearch() {
        val query = binding.searchEditText.text.toString().trim()
        if (query.isNotEmpty()) {
            viewModel.searchVideos(query)
            // Hide keyboard
            binding.searchEditText.clearFocus()
        }
    }
    
    private fun setupSwipeRefresh() {
        binding.swipeRefreshLayout.setOnRefreshListener {
            viewModel.refresh()
        }
        
        // Set colors
        binding.swipeRefreshLayout.setColorSchemeResources(
            R.color.colorPrimary,
            R.color.colorAccent
        )
    }
    
    private fun observeViewModel() {
        // Observe videos
        viewModel.videos.observe(this) { videos ->
            videoAdapter.submitList(videos)
            
            binding.emptyView.visibility = 
                if (videos.isEmpty() && viewModel.isLoading.value != true) View.VISIBLE else View.GONE
        }
        
        // Observe categories
        viewModel.categories.observe(this) { categories ->
            categoryAdapter.submitList(categories)
        }
        
        // Observe statistics
        viewModel.statistics.observe(this) { statistics ->
            if (statistics != null) {
                binding.statsText.text = getString(
                    R.string.stats_format,
                    statistics.totalVideos,
                    statistics.totalPlays
                )
                binding.statsText.visibility = View.VISIBLE
            } else {
                binding.statsText.visibility = View.GONE
            }
        }
        
        // Observe loading state
        viewModel.isLoading.observe(this) { isLoading ->
            binding.swipeRefreshLayout.isRefreshing = isLoading
            
            // Show loading indicator for initial load
            binding.loadingView.visibility = 
                if (isLoading && videoAdapter.itemCount == 0) View.VISIBLE else View.GONE
        }
        
        // Observe errors
        viewModel.error.observe(this) { error ->
            if (error != null) {
                Toast.makeText(this, error, Toast.LENGTH_SHORT).show()
                viewModel.clearError()
            }
        }
    }
    
    private fun navigateToPlayer(video: Video) {
        val intent = Intent(this, PlayerActivity::class.java).apply {
            putExtra(PlayerActivity.EXTRA_VIDEO_ID, video.videoId)
        }
        startActivity(intent)
    }
}
