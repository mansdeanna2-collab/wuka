<template>
  <div class="video-management-page">
    <!-- Toolbar -->
    <div class="vm-toolbar">
      <div class="toolbar-left">
        <div class="search-box">
          <AppIcon name="search" :size="18" class="search-icon" />
          <input
            v-model="videoSearchKeyword"
            type="text"
            placeholder="搜索视频标题..."
            class="search-input"
            @keyup.enter="searchVideos"
          />
        </div>
        <div class="filter-box">
          <AppIcon name="filter" :size="16" class="filter-icon" />
          <select v-model="filterCategory" class="select-input" @change="applyCategoryFilter">
            <option value="">全部分类</option>
            <optgroup v-for="group in navGroups" :key="group.key" :label="group.label">
              <option v-for="sub in group.subcategories" :key="group.key + sub" :value="sub">
                {{ sub }}
              </option>
            </optgroup>
          </select>
        </div>
        <button class="btn btn-secondary" @click="searchVideos">
          <AppIcon name="refresh" :size="16" /> 刷新
        </button>
      </div>
      <button class="btn btn-primary" @click="openAddVideoModal">
        <AppIcon name="plus" :size="16" /> 添加视频
      </button>
    </div>

    <!-- Video List -->
    <div class="tab-content">
      <div class="list-header">
        <h3>
          <AppIcon name="film" :size="18" />
          {{ filterCategory ? `分类：${filterCategory}` : '全部视频' }}
        </h3>
        <span class="list-count">{{ managedVideos.length }} 个视频</span>
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
          <div v-else class="video-thumb-placeholder">
            <AppIcon name="film" :size="20" />
          </div>
          <div class="video-info">
            <span class="video-title">{{ video.video_title }}</span>
            <span class="video-meta">
              <span class="meta-tag">ID: {{ video.video_id }}</span>
              <span class="meta-tag category">{{ video.video_category || '未分类' }}</span>
              <span class="meta-tag">播放 {{ video.play_count || 0 }}</span>
            </span>
          </div>
          <div class="video-actions">
            <button class="btn btn-secondary btn-sm" @click="openEditVideoModal(video)">
              <AppIcon name="edit" :size="14" /> 编辑
            </button>
            <button class="btn btn-danger btn-sm" @click="confirmDeleteVideo(video)">
              <AppIcon name="trash" :size="14" /> 删除
            </button>
          </div>
        </div>

        <div v-if="managedVideos.length === 0" class="empty-state">
          <AppIcon name="film" :size="40" />
          <p>暂无视频数据</p>
        </div>
      </div>
    </div>

    <!-- Edit Video Modal -->
    <div v-if="showEditVideoModal" class="modal-overlay" @click.self="showEditVideoModal = false">
      <div class="modal">
        <div class="modal-header">
          <h3><AppIcon name="edit" :size="18" /> 编辑视频</h3>
          <button class="close-btn" @click="showEditVideoModal = false">
            <AppIcon name="x" :size="20" />
          </button>
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
            <CategoryPicker v-model="editingVideo.video_category" />
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
          <h3><AppIcon name="plus" :size="18" /> 添加视频</h3>
          <button class="close-btn" @click="showAddVideoModal = false">
            <AppIcon name="x" :size="20" />
          </button>
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
            <CategoryPicker v-model="newVideo.video_category" />
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
          <h3><AppIcon name="alert" :size="18" /> 确认删除</h3>
          <button class="close-btn" @click="showDeleteModal = false">
            <AppIcon name="x" :size="20" />
          </button>
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
import { getNavCategories, fetchNavCategories } from '@/utils/navCategoryManager'
import AppIcon from '@/components/AppIcon.vue'
import CategoryPicker from '@/components/admin/CategoryPicker.vue'
export default {
  name: 'VideoManagement',
  components: { AppIcon, CategoryPicker },
  data() {
    return {
      // Navigation category groups (power the filter + pickers)
      navGroups: [],

      // Video Management
      managedVideos: [],
      loadingVideos: false,
      videoSearchKeyword: '',
      filterCategory: '',

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
  mounted() {
    this.loadNavGroups()
    this.refreshNavGroups()
    this.searchVideos()
  },
  methods: {
    loadNavGroups() {
      const cats = getNavCategories() || []
      this.navGroups = cats.map(c => ({
        key: c.key,
        label: c.label,
        subcategories: Array.isArray(c.subcategories) ? c.subcategories : []
      }))
    },

    async refreshNavGroups() {
      // Pull the latest saved navigation categories so the filter and pickers
      // reflect what the admin configured, not just cached defaults.
      try {
        await fetchNavCategories()
        this.loadNavGroups()
      } catch (e) {
        console.error('Load nav categories error:', e)
      }
    },

    applyCategoryFilter() {
      this.searchVideos()
    },

    // Video Management
    async searchVideos() {
      this.loadingVideos = true

      try {
        let result
        if (this.videoSearchKeyword) {
          result = await videoApi.searchVideos(this.videoSearchKeyword, 50)
          let videos = extractArrayData(result)
          if (this.filterCategory) {
            videos = videos.filter(v => v.video_category === this.filterCategory)
          }
          this.managedVideos = videos
        } else if (this.filterCategory) {
          result = await videoApi.getCategoryVideosAdmin(this.filterCategory, 50)
          this.managedVideos = extractArrayData(result)
        } else {
          result = await videoApi.getVideos({ limit: 50 })
          this.managedVideos = extractArrayData(result)
        }
      } catch (e) {
        console.error('Search videos error:', e)
        this.showToast('加载视频失败', 'error')
      } finally {
        this.loadingVideos = false
      }
    },

    openAddVideoModal() {
      this.newVideo = {
        video_title: '',
        video_url: '',
        video_image: '',
        video_category: this.filterCategory || '',
        video_duration: ''
      }
      this.showAddVideoModal = true
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
        this.searchVideos()
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
        this.searchVideos()
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
        this.searchVideos()
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

/* Toolbar */
.vm-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 22px;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.search-box {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 12px;
  color: var(--admin-text-faint);
  pointer-events: none;
}

.search-input {
  padding: 10px 15px 10px 38px;
  min-width: 240px;
  background: var(--admin-surface);
  border: 1px solid var(--admin-border-strong);
  border-radius: var(--admin-radius-sm);
  color: var(--admin-text);
  font-size: 0.9em;
}

.filter-box {
  position: relative;
  display: flex;
  align-items: center;
}

.filter-icon {
  position: absolute;
  left: 12px;
  color: var(--admin-text-faint);
  pointer-events: none;
}

.select-input {
  padding: 10px 15px 10px 36px;
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

.search-input:focus,
.select-input:focus,
.form-input:focus {
  outline: none;
  border-color: var(--admin-primary);
  box-shadow: 0 0 0 3px var(--admin-primary-soft);
}

.form-input::placeholder,
.search-input::placeholder {
  color: var(--admin-text-faint);
}

/* Buttons */
.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 18px;
  border: none;
  border-radius: var(--admin-radius-sm);
  font-size: 0.9em;
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
  font-size: 0.82em;
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

/* List container */
.tab-content {
  background: var(--admin-surface);
  border-radius: var(--admin-radius);
  padding: 22px 25px;
  border: 1px solid var(--admin-border);
  box-shadow: var(--admin-shadow-sm);
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 18px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--admin-border);
}

.list-header h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  font-size: 1.1em;
  color: var(--admin-text);
}

.list-count {
  font-size: 0.85em;
  color: var(--admin-text-muted);
  padding: 3px 12px;
  background: var(--admin-surface-3);
  border-radius: 12px;
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
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  text-align: center;
  padding: 50px 20px;
  color: var(--admin-text-faint);
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
  transition: all 0.2s;
}

.video-item:hover {
  border-color: var(--admin-primary-border);
  box-shadow: var(--admin-shadow-sm);
}

.video-thumb {
  width: 90px;
  height: 52px;
  object-fit: cover;
  border-radius: 6px;
  background: var(--admin-surface-3);
  flex-shrink: 0;
}

.video-thumb-placeholder {
  width: 90px;
  height: 52px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  background: var(--admin-surface-3);
  color: var(--admin-text-faint);
  flex-shrink: 0;
}

.video-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.video-title {
  font-weight: 600;
  color: var(--admin-text);
  font-size: 0.92em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.video-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.meta-tag {
  font-size: 0.75em;
  color: var(--admin-text-muted);
  padding: 2px 8px;
  background: var(--admin-surface-2);
  border-radius: 10px;
}

.meta-tag.category {
  color: var(--admin-accent-ink);
  background: var(--admin-accent-soft);
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
  overflow: visible;
  display: flex;
  flex-direction: column;
  box-shadow: var(--admin-shadow-lg);
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
  border-radius: var(--admin-radius) var(--admin-radius) 0 0;
}

.modal-header h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  font-size: 1.1em;
  color: var(--admin-text);
}

.close-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: none;
  border: none;
  color: var(--admin-text-faint);
  cursor: pointer;
  border-radius: var(--admin-radius-sm);
}

.close-btn:hover {
  color: var(--admin-text);
  background: var(--admin-surface-3);
}

.modal-body {
  padding: 20px;
  overflow-y: auto;
  overflow-x: visible;
  flex: 1;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 15px 20px;
  background: var(--admin-surface-2);
  border-top: 1px solid var(--admin-border);
  border-radius: 0 0 var(--admin-radius) var(--admin-radius);
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
  padding: 10px 15px;
  background: var(--admin-surface);
  border: 1px solid var(--admin-border-strong);
  border-radius: var(--admin-radius-sm);
  color: var(--admin-text);
  font-size: 0.9em;
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
  .vm-toolbar {
    flex-direction: column;
    align-items: stretch;
  }

  .toolbar-left {
    flex-direction: column;
    align-items: stretch;
  }

  .search-input {
    min-width: 0;
    width: 100%;
  }

  .select-input {
    width: 100%;
  }

  .tab-content {
    padding: 15px;
  }

  .video-item {
    flex-wrap: wrap;
  }

  .video-thumb,
  .video-thumb-placeholder {
    width: 70px;
    height: 40px;
  }

  .video-actions {
    width: 100%;
    justify-content: flex-end;
  }
}
</style>
