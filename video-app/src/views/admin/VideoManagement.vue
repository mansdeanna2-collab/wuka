<template>
  <div class="video-management-page">
    <!-- Tab Navigation -->
    <div class="tab-nav">
      <button 
        v-for="tab in tabs" 
        :key="tab.key"
        :class="['tab-btn', { active: activeTab === tab.key }]"
        @click="activeTab = tab.key"
      >
        <span class="tab-icon">{{ tab.icon }}</span>
        {{ tab.label }}
      </button>
    </div>

    <!-- Category Statistics Tab -->
    <div v-if="activeTab === 'stats'" class="tab-content">
      <div class="section-header">
        <h3>📊 分类视频统计</h3>
        <button class="btn btn-secondary btn-sm" @click="loadCategoryStats">
          🔄 刷新
        </button>
      </div>
      
      <div v-if="loadingStats" class="loading-state">
        <div class="loading-spinner"></div>
        <p>加载中...</p>
      </div>
      
      <div v-else class="stats-grid">
        <div 
          v-for="cat in categoryStats" 
          :key="cat.video_category"
          class="stat-card"
        >
          <img 
            v-if="cat.sample_image" 
            :src="formatImageUrl(cat.sample_image)" 
            :alt="cat.video_category"
            class="stat-image"
            @error="handleImageError"
          />
          <div v-else class="stat-image-placeholder">
            🎬
          </div>
          <div class="stat-info">
            <span class="stat-category">{{ cat.video_category || '未分类' }}</span>
            <span class="stat-count">{{ cat.video_count }} 个视频</span>
          </div>
          <button 
            class="btn btn-primary btn-sm"
            @click="viewCategoryVideos(cat.video_category)"
          >
            查看
          </button>
        </div>
        
        <div v-if="categoryStats.length === 0" class="empty-state">
          <p>暂无分类数据</p>
        </div>
      </div>
    </div>

    <!-- Duplicate Detection Tab -->
    <div v-if="activeTab === 'duplicates'" class="tab-content">
      <div class="section-header">
        <h3>🔍 重复视频检测</h3>
        <div class="header-actions">
          <select v-model="duplicateType" class="select-input">
            <option value="title">按标题查重</option>
            <option value="image">按图片查重</option>
          </select>
          <button class="btn btn-primary btn-sm" @click="checkDuplicates">
            开始检测
          </button>
        </div>
      </div>
      
      <div v-if="loadingDuplicates" class="loading-state">
        <div class="loading-spinner"></div>
        <p>检测中...</p>
      </div>
      
      <div v-else-if="duplicateGroups.length > 0" class="duplicates-list">
        <div 
          v-for="(group, index) in duplicateGroups" 
          :key="index"
          class="duplicate-group"
        >
          <div class="group-header">
            <span class="group-title">
              {{ group.duplicate_type === 'title' ? '标题' : '图片' }}: 
              {{ truncateText(group.duplicate_value, 50) }}
            </span>
            <span class="group-count">{{ group.count }} 个重复</span>
          </div>
          <div class="group-videos">
            <div 
              v-for="video in group.videos" 
              :key="video.video_id"
              class="video-item"
            >
              <img 
                v-if="video.video_image" 
                :src="formatImageUrl(video.video_image)" 
                :alt="video.video_title"
                class="video-thumb"
                @error="handleImageError"
              />
              <div class="video-info">
                <span class="video-title">{{ video.video_title }}</span>
                <span class="video-meta">ID: {{ video.video_id }} | {{ video.video_category }}</span>
              </div>
              <button 
                class="btn btn-danger btn-sm"
                @click="confirmDeleteVideo(video)"
              >
                删除
              </button>
            </div>
          </div>
        </div>
      </div>
      
      <div v-else class="empty-state">
        <p>{{ duplicateCheckDone ? '未发现重复视频' : '点击"开始检测"查找重复视频' }}</p>
      </div>
    </div>

    <!-- Video Management Tab -->
    <div v-if="activeTab === 'manage'" class="tab-content">
      <div class="section-header">
        <h3>🎬 视频管理</h3>
        <button class="btn btn-primary" @click="showAddVideoModal = true">
          ➕ 添加视频
        </button>
      </div>
      
      <div class="search-bar">
        <input 
          v-model="videoSearchKeyword" 
          type="text" 
          placeholder="搜索视频标题..."
          class="search-input"
          @keyup.enter="searchVideos"
        />
        <button class="btn btn-primary" @click="searchVideos">搜索</button>
      </div>
      
      <div v-if="loadingVideos" class="loading-state">
        <div class="loading-spinner"></div>
        <p>加载中...</p>
      </div>
      
      <div v-else class="videos-list">
        <div 
          v-for="video in managedVideos" 
          :key="video.video_id"
          class="video-item"
        >
          <img 
            v-if="video.video_image" 
            :src="formatImageUrl(video.video_image)" 
            :alt="video.video_title"
            class="video-thumb"
            @error="handleImageError"
          />
          <div class="video-info">
            <span class="video-title">{{ video.video_title }}</span>
            <span class="video-meta">
              ID: {{ video.video_id }} | {{ video.video_category }} | 播放: {{ video.play_count || 0 }}
            </span>
          </div>
          <button 
            class="btn btn-danger btn-sm"
            @click="confirmDeleteVideo(video)"
          >
            删除
          </button>
        </div>
        
        <div v-if="managedVideos.length === 0" class="empty-state">
          <p>暂无视频数据</p>
        </div>
      </div>
    </div>

    <!-- Category Videos Modal -->
    <div v-if="showCategoryModal" class="modal-overlay" @click.self="closeCategoryModal">
      <div class="modal modal-large">
        <div class="modal-header">
          <h3>{{ viewingCategory || '未分类' }} - 视频列表</h3>
          <button class="close-btn" @click="closeCategoryModal">×</button>
        </div>
        <div class="modal-body">
          <div v-if="loadingCategoryVideos" class="loading-state">
            <div class="loading-spinner"></div>
            <p>加载中...</p>
          </div>
          <div v-else class="videos-list">
            <div 
              v-for="video in categoryVideos" 
              :key="video.video_id"
              class="video-item"
            >
              <img 
                v-if="video.video_image" 
                :src="formatImageUrl(video.video_image)" 
                :alt="video.video_title"
                class="video-thumb"
                @error="handleImageError"
              />
              <div class="video-info">
                <span class="video-title">{{ video.video_title }}</span>
                <span class="video-meta">
                  ID: {{ video.video_id }} | 分类: {{ video.video_category || '未分类' }} | 播放: {{ video.play_count || 0 }}
                </span>
                <span class="video-meta">
                  时长: {{ video.video_duration || '未知' }} | 上传: {{ video.upload_time || '未知' }}
                </span>
              </div>
              <div class="video-actions">
                <button 
                  class="btn btn-secondary btn-sm"
                  @click="openEditVideoModal(video)"
                >
                  编辑
                </button>
                <button 
                  class="btn btn-danger btn-sm"
                  @click="confirmDeleteVideo(video)"
                >
                  删除
                </button>
              </div>
            </div>
            <div v-if="categoryVideos.length === 0" class="empty-state">
              <p>该分类暂无视频</p>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeCategoryModal">关闭</button>
        </div>
      </div>
    </div>

    <!-- Edit Video Modal -->
    <div v-if="showEditVideoModal" class="modal-overlay" @click.self="showEditVideoModal = false">
      <div class="modal">
        <div class="modal-header">
          <h3>编辑视频</h3>
          <button class="close-btn" @click="showEditVideoModal = false">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>视频ID</label>
            <input :value="editingVideo.video_id" type="text" class="form-input" disabled />
          </div>
          <div class="form-group">
            <label>视频标题 *</label>
            <input v-model="editingVideo.video_title" type="text" class="form-input" placeholder="输入视频标题" />
          </div>
          <div class="form-group">
            <label>视频URL *</label>
            <input v-model="editingVideo.video_url" type="text" class="form-input" placeholder="输入视频播放地址" />
          </div>
          <div class="form-group">
            <label>封面图片URL</label>
            <input v-model="editingVideo.video_image" type="text" class="form-input" placeholder="输入封面图片地址" />
          </div>
          <div class="form-group">
            <label>分类</label>
            <input v-model="editingVideo.video_category" type="text" class="form-input" list="category-options" placeholder="选择已有分类或输入新分类" />
          </div>
          <div class="form-group">
            <label>时长</label>
            <input v-model="editingVideo.video_duration" type="text" class="form-input" placeholder="例如: 01:30:00" />
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showEditVideoModal = false">取消</button>
          <button class="btn btn-primary" @click="updateVideo">保存</button>
        </div>
      </div>
    </div>

    <!-- Add Video Modal -->
    <div v-if="showAddVideoModal" class="modal-overlay" @click.self="showAddVideoModal = false">
      <div class="modal">
        <div class="modal-header">
          <h3>添加视频</h3>
          <button class="close-btn" @click="showAddVideoModal = false">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>视频标题 *</label>
            <input v-model="newVideo.video_title" type="text" class="form-input" placeholder="输入视频标题" />
          </div>
          <div class="form-group">
            <label>视频URL *</label>
            <input v-model="newVideo.video_url" type="text" class="form-input" placeholder="输入视频播放地址" />
          </div>
          <div class="form-group">
            <label>封面图片URL</label>
            <input v-model="newVideo.video_image" type="text" class="form-input" placeholder="输入封面图片地址" />
          </div>
          <div class="form-group">
            <label>分类</label>
            <input v-model="newVideo.video_category" type="text" class="form-input" list="category-options" placeholder="选择已有分类或输入新分类" />
          </div>
          <div class="form-group">
            <label>时长</label>
            <input v-model="newVideo.video_duration" type="text" class="form-input" placeholder="例如: 01:30:00" />
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showAddVideoModal = false">取消</button>
          <button class="btn btn-primary" @click="addVideo">添加</button>
        </div>
      </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <div v-if="showDeleteModal" class="modal-overlay" @click.self="showDeleteModal = false">
      <div class="modal modal-small">
        <div class="modal-header">
          <h3>确认删除</h3>
          <button class="close-btn" @click="showDeleteModal = false">×</button>
        </div>
        <div class="modal-body">
          <p>确定要删除视频"{{ deletingVideo?.video_title }}"吗？</p>
          <p class="warning-text">此操作不可恢复！</p>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showDeleteModal = false">取消</button>
          <button class="btn btn-danger" @click="deleteVideo">确认删除</button>
        </div>
      </div>
    </div>

    <!-- Shared category options for datalist pickers -->
    <datalist id="category-options">
      <option v-for="cat in categoryOptions" :key="cat" :value="cat" />
    </datalist>

    <!-- Toast Notification -->
    <transition name="toast">
      <div v-if="toastMessage" class="toast-message" :class="toastType">
        {{ toastMessage }}
      </div>
    </transition>
  </div>
</template>

<script>
import { videoApi } from '@/api'
import { extractArrayData } from '@/utils/apiUtils'
import { formatImageUrl } from '@/utils/imageUtils'

export default {
  name: 'VideoManagement',
  data() {
    return {
      activeTab: 'stats',
      tabs: [
        { key: 'stats', label: '分类统计', icon: '📊' },
        { key: 'duplicates', label: '重复检测', icon: '🔍' },
        { key: 'manage', label: '视频管理', icon: '🎬' }
      ],
      
      // Category Stats
      categoryStats: [],
      loadingStats: false,
      
      // Category Videos Modal
      showCategoryModal: false,
      viewingCategory: '',
      categoryVideos: [],
      loadingCategoryVideos: false,
      
      // Duplicate Detection
      duplicateType: 'title',
      duplicateGroups: [],
      loadingDuplicates: false,
      duplicateCheckDone: false,
      
      // Video Management
      managedVideos: [],
      loadingVideos: false,
      videoSearchKeyword: '',
      showAddVideoModal: false,
      newVideo: {
        video_title: '',
        video_url: '',
        video_image: '',
        video_category: '',
        video_duration: ''
      },
      
      // Delete confirmation
      showDeleteModal: false,
      deletingVideo: null,
      
      // Edit video modal
      showEditVideoModal: false,
      editingVideo: {
        video_id: null,
        video_title: '',
        video_url: '',
        video_image: '',
        video_category: '',
        video_duration: ''
      },
      
      // Toast
      toastMessage: '',
      toastType: ''
    }
  },
  computed: {
    // Existing category names (from stats) used to power the category picker
    categoryOptions() {
      return this.categoryStats
        .map(cat => cat.video_category)
        .filter(name => name && name !== '未分类')
    }
  },
  mounted() {
    this.loadCategoryStats()
  },
  methods: {
    // Category Statistics
    async loadCategoryStats() {
      this.loadingStats = true
      try {
        const result = await videoApi.getCategoryStats()
        this.categoryStats = extractArrayData(result)
      } catch (e) {
        console.error('Load category stats error:', e)
        this.showToast('加载分类统计失败', 'error')
      } finally {
        this.loadingStats = false
      }
    },
    
    async viewCategoryVideos(category) {
      this.viewingCategory = category
      this.showCategoryModal = true
      this.loadingCategoryVideos = true
      
      try {
        const result = await videoApi.getCategoryVideosAdmin(category, 50)
        this.categoryVideos = extractArrayData(result)
      } catch (e) {
        console.error('Load category videos error:', e)
        this.showToast('加载视频列表失败', 'error')
      } finally {
        this.loadingCategoryVideos = false
      }
    },
    
    closeCategoryModal() {
      this.showCategoryModal = false
      this.viewingCategory = ''
      this.categoryVideos = []
    },
    
    // Duplicate Detection
    async checkDuplicates() {
      this.loadingDuplicates = true
      this.duplicateCheckDone = false
      
      try {
        const result = await videoApi.getDuplicateVideos(this.duplicateType)
        this.duplicateGroups = extractArrayData(result)
        this.duplicateCheckDone = true
        
        if (this.duplicateGroups.length === 0) {
          this.showToast('未发现重复视频', 'success')
        } else {
          this.showToast(`发现 ${this.duplicateGroups.length} 组重复视频`, 'info')
        }
      } catch (e) {
        console.error('Check duplicates error:', e)
        this.showToast('检测重复视频失败', 'error')
      } finally {
        this.loadingDuplicates = false
      }
    },
    
    // Video Management
    async searchVideos() {
      this.loadingVideos = true
      
      try {
        let result
        if (this.videoSearchKeyword) {
          result = await videoApi.searchVideos(this.videoSearchKeyword, 50)
        } else {
          result = await videoApi.getVideos({ limit: 50 })
        }
        this.managedVideos = extractArrayData(result)
      } catch (e) {
        console.error('Search videos error:', e)
        this.showToast('搜索视频失败', 'error')
      } finally {
        this.loadingVideos = false
      }
    },
    
    async addVideo() {
      if (!this.newVideo.video_title || !this.newVideo.video_url) {
        this.showToast('请填写必填字段', 'error')
        return
      }
      
      try {
        await videoApi.addVideo(this.newVideo)
        this.showToast('视频添加成功', 'success')
        this.showAddVideoModal = false
        this.newVideo = {
          video_title: '',
          video_url: '',
          video_image: '',
          video_category: '',
          video_duration: ''
        }
        // Refresh stats and video list
        this.loadCategoryStats()
        if (this.activeTab === 'manage') {
          this.searchVideos()
        }
      } catch (e) {
        console.error('Add video error:', e)
        this.showToast('添加视频失败', 'error')
      }
    },
    
    confirmDeleteVideo(video) {
      this.deletingVideo = video
      this.showDeleteModal = true
    },
    
    async deleteVideo() {
      if (!this.deletingVideo) return
      
      try {
        await videoApi.deleteVideo(this.deletingVideo.video_id)
        this.showToast('视频删除成功', 'success')
        this.showDeleteModal = false
        this.deletingVideo = null
        
        // Refresh data
        this.loadCategoryStats()
        if (this.activeTab === 'duplicates') {
          this.checkDuplicates()
        }
        if (this.activeTab === 'manage') {
          this.searchVideos()
        }
        // Refresh category videos if modal is open
        if (this.showCategoryModal && this.viewingCategory) {
          this.viewCategoryVideos(this.viewingCategory)
        }
      } catch (e) {
        console.error('Delete video error:', e)
        this.showToast('删除视频失败', 'error')
      }
    },
    
    // Open edit video modal
    openEditVideoModal(video) {
      this.editingVideo = {
        video_id: video.video_id,
        video_title: video.video_title || '',
        video_url: video.video_url || '',
        video_image: video.video_image || '',
        video_category: video.video_category || '',
        video_duration: video.video_duration || ''
      }
      this.showEditVideoModal = true
    },
    
    // Update video
    async updateVideo() {
      if (!this.editingVideo.video_id || !this.editingVideo.video_title || !this.editingVideo.video_url) {
        this.showToast('请填写必填字段', 'error')
        return
      }
      
      try {
        await videoApi.updateVideo(this.editingVideo.video_id, this.editingVideo)
        this.showToast(`视频 "${this.truncateText(this.editingVideo.video_title, 20)}" 更新成功`, 'success')
        this.showEditVideoModal = false
        
        // Refresh data
        this.loadCategoryStats()
        if (this.activeTab === 'manage') {
          this.searchVideos()
        }
        // Refresh category videos if modal is open
        if (this.showCategoryModal && this.viewingCategory) {
          this.viewCategoryVideos(this.viewingCategory)
        }
      } catch (e) {
        console.error('Update video error:', e)
        this.showToast('更新视频失败', 'error')
      }
    },
    
    // Utility methods
    truncateText(text, maxLength) {
      if (!text) return ''
      return text.length > maxLength ? text.substring(0, maxLength) + '...' : text
    },
    
    // Format image URL to handle base64 and special URL formats
    formatImageUrl(url) {
      return formatImageUrl(url)
    },
    
    handleImageError(e) {
      // Use a transparent 1x1 pixel data URI instead of empty string to avoid browser loading current page
      e.target.src = 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7'
      e.target.style.background = 'var(--admin-surface-3)'
    },
    
    showToast(message, type = 'info') {
      this.toastMessage = message
      this.toastType = type
      setTimeout(() => {
        this.toastMessage = ''
        this.toastType = ''
      }, 2500)
    }
  }
}
</script>

<style scoped>
.video-management-page {
  max-width: 1200px;
}

/* Tab Navigation */
.tab-nav {
  display: flex;
  gap: 10px;
  margin-bottom: 25px;
  flex-wrap: wrap;
}

.tab-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  background: var(--admin-surface);
  border: 1px solid var(--admin-border);
  border-radius: var(--admin-radius-sm);
  color: var(--admin-text-muted);
  font-size: 0.95em;
  cursor: pointer;
  transition: all 0.2s;
}

.tab-btn:hover {
  background: var(--admin-surface-2);
  color: var(--admin-text);
}

.tab-btn.active {
  background: var(--admin-primary-soft);
  border-color: var(--admin-primary-border);
  color: var(--admin-primary-dark);
  font-weight: 600;
}

.tab-icon {
  font-size: 1.2em;
}

/* Tab Content */
.tab-content {
  background: var(--admin-surface);
  border-radius: var(--admin-radius);
  padding: 25px;
  border: 1px solid var(--admin-border);
  box-shadow: var(--admin-shadow-sm);
}

/* Section Header */
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-header h3 {
  margin: 0;
  font-size: 1.2em;
  color: var(--admin-text);
}

.header-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

/* Buttons */
.btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border: none;
  border-radius: var(--admin-radius-sm);
  font-size: 0.95em;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-sm {
  padding: 6px 12px;
  font-size: 0.85em;
}

.btn-primary {
  background: linear-gradient(135deg, var(--admin-primary) 0%, var(--admin-primary-dark) 100%);
  color: #fff;
}

.btn-primary:hover {
  filter: brightness(1.05);
  box-shadow: var(--admin-shadow-sm);
}

.btn-secondary {
  background: var(--admin-surface);
  color: var(--admin-text-muted);
  border: 1px solid var(--admin-border-strong);
}

.btn-secondary:hover {
  background: var(--admin-surface-2);
  color: var(--admin-text);
}

.btn-danger {
  background: linear-gradient(135deg, var(--admin-danger) 0%, var(--admin-danger-dark) 100%);
  color: #fff;
}

.btn-danger:hover {
  filter: brightness(1.05);
  box-shadow: var(--admin-shadow-sm);
}

/* Form inputs */
.select-input,
.search-input,
.form-input {
  padding: 10px 15px;
  background: var(--admin-surface);
  border: 1px solid var(--admin-border-strong);
  border-radius: var(--admin-radius-sm);
  color: var(--admin-text);
  font-size: 0.9em;
}

.select-input option {
  background-color: var(--admin-surface);
  color: var(--admin-text);
}

.select-input:focus,
.search-input:focus,
.form-input:focus {
  outline: none;
  border-color: var(--admin-primary);
  box-shadow: 0 0 0 3px var(--admin-primary-soft);
}

.form-input::placeholder,
.search-input::placeholder {
  color: var(--admin-text-faint);
}

.search-bar {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.search-input {
  flex: 1;
  max-width: 400px;
}

/* Loading State */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 20px;
}

.loading-state p {
  margin-top: 15px;
  color: var(--admin-text-muted);
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--admin-border);
  border-radius: 50%;
  border-top-color: var(--admin-primary);
  animation: spin 1s ease-in-out infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Empty State */
.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: var(--admin-text-muted);
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 15px;
}

.stat-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  background: var(--admin-surface-2);
  border: 1px solid var(--admin-border);
  border-radius: var(--admin-radius);
  transition: all 0.2s;
}

.stat-card:hover {
  border-color: var(--admin-primary-border);
  box-shadow: var(--admin-shadow-sm);
}

.stat-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-category {
  font-weight: 600;
  color: var(--admin-text);
}

.stat-count {
  font-size: 0.85em;
  color: var(--admin-accent-ink);
}

.stat-image {
  width: 60px;
  height: 40px;
  object-fit: cover;
  border-radius: 6px;
  background: var(--admin-surface-3);
  flex-shrink: 0;
}

.stat-image-placeholder {
  width: 60px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--admin-surface-3);
  border-radius: 6px;
  font-size: 1.2em;
  flex-shrink: 0;
}

/* Duplicates List */
.duplicates-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.duplicate-group {
  background: var(--admin-surface-2);
  border: 1px solid var(--admin-border);
  border-radius: var(--admin-radius);
  overflow: hidden;
}

.group-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 15px;
  background: var(--admin-danger-soft);
  border-bottom: 1px solid var(--admin-border);
}

.group-title {
  font-weight: 500;
  color: var(--admin-text);
  font-size: 0.9em;
}

.group-count {
  font-size: 0.85em;
  color: var(--admin-danger-dark);
  font-weight: 600;
}

.group-videos {
  padding: 10px;
}

/* Video Items */
.videos-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.video-item {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 12px 15px;
  background: var(--admin-surface);
  border: 1px solid var(--admin-border);
  border-radius: var(--admin-radius-sm);
}

.video-thumb {
  width: 80px;
  height: 45px;
  object-fit: cover;
  border-radius: 4px;
  background: var(--admin-surface-3);
  flex-shrink: 0;
}

.video-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.video-title {
  font-weight: 500;
  color: var(--admin-text);
  font-size: 0.9em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.video-meta {
  font-size: 0.8em;
  color: var(--admin-text-muted);
}

.video-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(15, 23, 42, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal {
  background: var(--admin-surface);
  border-radius: var(--admin-radius);
  width: 100%;
  max-width: 500px;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: var(--admin-shadow-lg);
}

.modal-large {
  max-width: 800px;
}

.modal-small {
  max-width: 400px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  background: var(--admin-surface-2);
  border-bottom: 1px solid var(--admin-border);
}

.modal-header h3 {
  margin: 0;
  font-size: 1.1em;
  color: var(--admin-text);
}

.close-btn {
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: none;
  border: none;
  color: var(--admin-text-faint);
  font-size: 1.5em;
  cursor: pointer;
}

.close-btn:hover {
  color: var(--admin-text);
}

.modal-body {
  padding: 20px;
  overflow-y: auto;
  flex: 1;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 15px 20px;
  background: var(--admin-surface-2);
  border-top: 1px solid var(--admin-border);
}

/* Form */
.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: var(--admin-text);
  font-size: 0.9em;
}

.form-input {
  width: 100%;
}

.warning-text {
  color: var(--admin-danger-dark);
  font-size: 0.9em;
}

/* Toast */
.toast-message {
  position: fixed;
  bottom: 100px;
  left: 50%;
  transform: translateX(-50%);
  background: #1e293b;
  color: #fff;
  padding: 12px 24px;
  border-radius: var(--admin-radius-sm);
  font-size: 0.9em;
  box-shadow: var(--admin-shadow-lg);
  z-index: 2000;
}

.toast-message.success {
  background: var(--admin-success);
}

.toast-message.error {
  background: var(--admin-danger);
}

.toast-message.info {
  background: var(--admin-accent-ink);
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(20px);
}

/* Mobile responsive */
@media (max-width: 768px) {
  .tab-nav {
    gap: 8px;
  }

  .tab-btn {
    padding: 10px 15px;
    font-size: 0.85em;
  }

  .tab-content {
    padding: 15px;
  }

  .section-header {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }

  .header-actions {
    width: 100%;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .video-item {
    flex-wrap: wrap;
  }

  .video-thumb {
    width: 60px;
    height: 34px;
  }
}
</style>
