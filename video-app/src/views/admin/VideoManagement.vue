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
        <div class="list-header-actions">
          <label v-if="managedVideos.length > 0" class="select-all-label">
            <input
              type="checkbox"
              :checked="allSelected"
              :indeterminate.prop="someSelected"
              @change="toggleSelectAll"
            />
            全选
          </label>
          <button
            v-if="selectedIds.length > 0"
            class="btn btn-danger btn-sm"
            @click="confirmBatchDelete"
          >
            <AppIcon name="trash" :size="14" /> 删除选中 ({{ selectedIds.length }})
          </button>
          <span class="list-count">共 {{ totalVideos }} 个视频</span>
        </div>
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
          :class="{ selected: isSelected(video.video_id) }"
        >
          <label class="video-select" @click.stop>
            <input
              type="checkbox"
              :checked="isSelected(video.video_id)"
              @change="toggleSelect(video.video_id)"
            />
          </label>
          <img
            v-if="video.video_image"
            :src="formatImageUrl(video.video_image)"
            :alt="video.video_title"
            class="video-thumb"
            referrerpolicy="no-referrer"
            loading="lazy"
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
              <span v-if="video.video_duration" class="meta-tag">时长 {{ video.video_duration }}</span>
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

      <!-- Pagination -->
      <div v-if="!loadingVideos && totalPages > 1" class="pagination">
        <button
          class="page-btn"
          :disabled="currentPage === 1"
          @click="goToPage(1)"
        >
          首页
        </button>
        <button
          class="page-btn"
          :disabled="currentPage === 1"
          @click="goToPage(currentPage - 1)"
        >
          上一页
        </button>
        <button
          v-if="pageNumbers[0] > 1"
          class="page-btn"
          @click="goToPage(pageNumbers[0] - 1)"
        >
          …
        </button>
        <button
          v-for="page in pageNumbers"
          :key="page"
          class="page-btn"
          :class="{ active: page === currentPage }"
          @click="goToPage(page)"
        >
          {{ page }}
        </button>
        <button
          v-if="pageNumbers[pageNumbers.length - 1] < totalPages"
          class="page-btn"
          @click="goToPage(pageNumbers[pageNumbers.length - 1] + 1)"
        >
          …
        </button>
        <button
          class="page-btn"
          :disabled="currentPage === totalPages"
          @click="goToPage(currentPage + 1)"
        >
          下一页
        </button>
        <button
          class="page-btn"
          :disabled="currentPage === totalPages"
          @click="goToPage(totalPages)"
        >
          末页
        </button>
        <span class="page-info">第 {{ currentPage }} / {{ totalPages }} 页</span>
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
            <input
              v-model="editingVideo.video_url"
              type="text"
              class="form-input"
              placeholder="输入视频播放地址"
              @blur="autoDetectDuration(editingVideo)"
            />
          </div>
          <div class="form-group">
            <label>封面图片URL</label>
            <input v-model="editingVideo.video_image" type="text" class="form-input" placeholder="输入封面图片地址" />
            <div v-if="editingVideo.video_image" class="image-preview">
              <img
                :src="formatImageUrl(editingVideo.video_image)"
                alt="封面预览"
                referrerpolicy="no-referrer"
                @error="handleImageError"
              />
            </div>
          </div>
          <div class="form-group">
            <label>分类</label>
            <CategoryPicker v-model="editingVideo.video_category" />
          </div>
          <div class="form-group">
            <label>时长</label>
            <div class="duration-row">
              <input v-model="editingVideo.video_duration" type="text" class="form-input" placeholder="例如: 01:30:00" />
              <button
                class="btn btn-secondary btn-sm"
                :disabled="detectingDuration || !editingVideo.video_url"
                @click="detectDuration(editingVideo)"
              >
                <AppIcon name="refresh" :size="14" />
                {{ detectingDuration ? '读取中...' : '读取时长' }}
              </button>
            </div>
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
            <input
              v-model="newVideo.video_url"
              type="text"
              class="form-input"
              placeholder="输入视频播放地址"
              @blur="autoDetectDuration(newVideo)"
            />
          </div>
          <div class="form-group">
            <label>封面图片URL</label>
            <input v-model="newVideo.video_image" type="text" class="form-input" placeholder="输入封面图片地址" />
            <div v-if="newVideo.video_image" class="image-preview">
              <img
                :src="formatImageUrl(newVideo.video_image)"
                alt="封面预览"
                referrerpolicy="no-referrer"
                @error="handleImageError"
              />
            </div>
          </div>
          <div class="form-group">
            <label>分类</label>
            <CategoryPicker v-model="newVideo.video_category" />
          </div>
          <div class="form-group">
            <label>时长</label>
            <div class="duration-row">
              <input v-model="newVideo.video_duration" type="text" class="form-input" placeholder="例如: 01:30:00" />
              <button
                class="btn btn-secondary btn-sm"
                :disabled="detectingDuration || !newVideo.video_url"
                @click="detectDuration(newVideo)"
              >
                <AppIcon name="refresh" :size="14" />
                {{ detectingDuration ? '读取中...' : '读取时长' }}
              </button>
            </div>
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

    <!-- Batch Delete Confirmation Modal -->
    <div v-if="showBatchDeleteModal" class="modal-overlay" @click.self="showBatchDeleteModal = false">
      <div class="modal modal-small">
        <div class="modal-header">
          <h3><AppIcon name="alert" :size="18" /> 确认批量删除</h3>
          <button class="close-btn" @click="showBatchDeleteModal = false">
            <AppIcon name="x" :size="20" />
          </button>
        </div>
        <div class="modal-body">
          <p>确定要删除选中的 {{ selectedIds.length }} 个视频吗？</p>
          <p class="warning-text">此操作不可恢复！</p>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showBatchDeleteModal = false">取消</button>
          <button class="btn btn-danger" @click="batchDelete">确认删除</button>
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

      // Pagination
      currentPage: 1,
      pageSize: 50,
      totalVideos: 0,

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

      // Batch selection / delete
      selectedIds: [],
      showBatchDeleteModal: false,

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

      // Duration auto-detection state
      detectingDuration: false,

      // Toast
      toastMessage: '',
      toastType: ''
    }
  },
  computed: {
    // All currently listed videos are selected
    allSelected() {
      return (
        this.managedVideos.length > 0 &&
        this.managedVideos.every(v => this.selectedIds.includes(v.video_id))
      )
    },
    // Some (but not all) listed videos are selected -> show indeterminate state
    someSelected() {
      return this.selectedIds.length > 0 && !this.allSelected
    },
    // Total number of pages based on the server-reported total count
    totalPages() {
      return Math.max(1, Math.ceil(this.totalVideos / this.pageSize))
    },
    // Windowed list of page numbers to render around the current page
    pageNumbers() {
      const total = this.totalPages
      const current = this.currentPage
      const delta = 2
      const pages = []
      const start = Math.max(1, current - delta)
      const end = Math.min(total, current + delta)
      for (let i = start; i <= end; i++) {
        pages.push(i)
      }
      return pages
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
    // Reload the list from the first page whenever the search keyword or
    // category filter changes.
    async searchVideos() {
      this.currentPage = 1
      await this.loadVideos()
    },

    // Load the current page of videos, honoring the active search/category filter.
    async loadVideos() {
      this.loadingVideos = true
      // Reset any prior selection when the list changes
      this.clearSelection()

      const offset = (this.currentPage - 1) * this.pageSize

      try {
        let result
        if (this.videoSearchKeyword) {
          result = await videoApi.searchVideos(this.videoSearchKeyword, this.pageSize, offset)
          let videos = extractArrayData(result)
          if (this.filterCategory) {
            videos = videos.filter(v => v.video_category === this.filterCategory)
          }
          this.managedVideos = videos
        } else if (this.filterCategory) {
          result = await videoApi.getCategoryVideosAdmin(this.filterCategory, this.pageSize, offset)
          this.managedVideos = extractArrayData(result)
        } else {
          result = await videoApi.getVideos({ limit: this.pageSize, offset })
          this.managedVideos = extractArrayData(result)
        }
        this.totalVideos =
          typeof result?.total === 'number' ? result.total : this.managedVideos.length
      } catch (e) {
        console.error('Search videos error:', e)
        this.showToast('加载视频失败', 'error')
      } finally {
        this.loadingVideos = false
      }
    },

    // Navigate to a specific page (bounded to the valid range).
    async goToPage(page) {
      if (page < 1 || page > this.totalPages || page === this.currentPage) return
      this.currentPage = page
      await this.loadVideos()
      // Scroll back to the top of the list for better UX on long pages
      if (typeof window !== 'undefined') {
        window.scrollTo({ top: 0, behavior: 'smooth' })
      }
    },

    // After deleting items, keep the current page filled: step back a page when
    // the current page is emptied, otherwise reload to backfill from later pages.
    async reloadAfterDeletion() {
      if (this.managedVideos.length === 0 && this.currentPage > 1) {
        this.currentPage -= 1
      }
      await this.loadVideos()
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
        const result = await videoApi.addVideo(this.newVideo)
        // Clear API cache so lists (front & admin) reflect the new video immediately
        videoApi.clearCache()
        this.showToast('视频添加成功', 'success')
        this.showAddVideoModal = false

        // Optimistically prepend the new video to the list for instant UI feedback
        const newId = result?.data?.video_id
        const addedVideo = {
          ...this.newVideo,
          video_id: newId,
          play_count: 0
        }
        const matchesFilter = !this.filterCategory || addedVideo.video_category === this.filterCategory
        if (newId && matchesFilter && !this.videoSearchKeyword) {
          this.managedVideos = [addedVideo, ...this.managedVideos]
        }

        this.newVideo = {
          video_title: '',
          video_url: '',
          video_image: '',
          video_category: '',
          video_duration: ''
        }
        // Re-fetch in background to stay in sync with the server
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

    // ---- Batch selection helpers ----
    isSelected(id) {
      return this.selectedIds.includes(id)
    },

    toggleSelect(id) {
      const idx = this.selectedIds.indexOf(id)
      if (idx === -1) {
        this.selectedIds.push(id)
      } else {
        this.selectedIds.splice(idx, 1)
      }
    },

    toggleSelectAll() {
      if (this.allSelected) {
        this.selectedIds = []
      } else {
        this.selectedIds = this.managedVideos.map(v => v.video_id)
      }
    },

    clearSelection() {
      this.selectedIds = []
    },

    confirmBatchDelete() {
      if (this.selectedIds.length === 0) return
      this.showBatchDeleteModal = true
    },

    async batchDelete() {
      if (this.selectedIds.length === 0) return

      const ids = [...this.selectedIds]
      try {
        const result = await videoApi.batchDeleteVideos(ids)
        // Clear API cache so lists reflect the deletion immediately
        videoApi.clearCache()
        const deleted = result?.data?.deleted_count ?? ids.length
        // Remove deleted items from the local list instantly (real-time UI update)
        const idSet = new Set(ids)
        this.managedVideos = this.managedVideos.filter(v => !idSet.has(v.video_id))
        this.totalVideos = Math.max(0, this.totalVideos - deleted)
        this.clearSelection()
        this.showBatchDeleteModal = false
        this.showToast(`成功删除 ${deleted} 个视频`, 'success')
        // Refresh the page so it backfills from later pages (or steps back when empty)
        await this.reloadAfterDeletion()
      } catch (e) {
        console.error('Batch delete error:', e)
        this.showToast('批量删除失败', 'error')
      }
    },

    async deleteVideo() {
      if (!this.deletingVideo) return

      try {
        await videoApi.deleteVideo(this.deletingVideo.video_id)
        // Clear API cache so lists reflect the deletion immediately
        videoApi.clearCache()
        // Remove from the local list instantly (real-time UI update)
        const deletedId = this.deletingVideo.video_id
        this.managedVideos = this.managedVideos.filter(v => v.video_id !== deletedId)
        this.totalVideos = Math.max(0, this.totalVideos - 1)
        // Also drop it from any pending batch selection
        this.selectedIds = this.selectedIds.filter(id => id !== deletedId)
        this.showToast('视频删除成功', 'success')
        this.showDeleteModal = false
        this.deletingVideo = null
        // Refresh the page so it backfills from later pages (or steps back when empty)
        await this.reloadAfterDeletion()
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
        // Clear API cache so lists reflect the update immediately
        videoApi.clearCache()
        // Patch the local list item instantly (real-time UI update)
        const idx = this.managedVideos.findIndex(v => v.video_id === this.editingVideo.video_id)
        if (idx !== -1) {
          this.managedVideos.splice(idx, 1, { ...this.managedVideos[idx], ...this.editingVideo })
        }
        this.showToast(`视频 "${this.truncateText(this.editingVideo.video_title, 20)}" 更新成功`, 'success')
        this.showEditVideoModal = false
      } catch (e) {
        console.error('Update video error:', e)
        this.showToast('更新视频失败', 'error')
      }
    },

    // Auto-detect duration on URL blur when the duration field is still empty
    autoDetectDuration(target) {
      if (target.video_url && !target.video_duration) {
        this.detectDuration(target, true)
      }
    },

    // Read the real duration from the video file's metadata
    async detectDuration(target, silent = false) {
      const url = (target.video_url || '').trim()
      if (!url || this.detectingDuration) return
      if (!url.startsWith('http://') && !url.startsWith('https://')) {
        if (!silent) this.showToast('请输入有效的视频地址', 'error')
        return
      }

      this.detectingDuration = true
      try {
        const seconds = await this.loadVideoDuration(url)
        target.video_duration = this.formatDurationHMS(seconds)
        if (!silent) this.showToast('时长读取成功', 'success')
      } catch (e) {
        console.warn('Detect duration failed:', e)
        if (!silent) this.showToast('无法读取视频时长，请手动填写', 'error')
      } finally {
        this.detectingDuration = false
      }
    },

    // Load video metadata and resolve its duration.
    // Uses a detached <video> element for regular files, and hls.js for
    // .m3u8 streams on browsers without native HLS support (e.g. Chrome).
    loadVideoDuration(url) {
      const isHls = url.toLowerCase().includes('.m3u8')
      const probe = document.createElement('video')
      const nativeHls = !!(
        probe.canPlayType('application/vnd.apple.mpegurl') ||
        probe.canPlayType('application/x-mpegURL')
      )
      if (isHls && !nativeHls) {
        return this.loadHlsDuration(url)
      }
      return new Promise((resolve, reject) => {
        probe.preload = 'metadata'

        const cleanup = () => {
          clearTimeout(timer)
          probe.onloadedmetadata = null
          probe.onerror = null
          probe.removeAttribute('src')
          probe.load()
        }

        const timer = setTimeout(() => {
          cleanup()
          reject(new Error('读取超时'))
        }, 20000)

        probe.onloadedmetadata = () => {
          const duration = probe.duration
          cleanup()
          if (isFinite(duration) && duration > 0) {
            resolve(duration)
          } else {
            reject(new Error('无法获取时长'))
          }
        }
        probe.onerror = () => {
          cleanup()
          reject(new Error('视频加载失败'))
        }
        probe.src = url
      })
    },

    // Resolve an HLS stream's total duration via hls.js manifest parsing
    async loadHlsDuration(url) {
      const Hls = (await import('hls.js')).default
      if (!Hls.isSupported()) {
        throw new Error('浏览器不支持HLS')
      }
      return new Promise((resolve, reject) => {
        const hls = new Hls({ enableWorker: false })

        const cleanup = () => {
          clearTimeout(timer)
          try {
            hls.destroy()
          } catch { /* ignore */ }
        }

        const timer = setTimeout(() => {
          cleanup()
          reject(new Error('读取超时'))
        }, 20000)

        hls.on(Hls.Events.LEVEL_LOADED, (event, data) => {
          const duration = data?.details?.totalduration
          cleanup()
          if (isFinite(duration) && duration > 0) {
            resolve(duration)
          } else {
            reject(new Error('无法获取时长'))
          }
        })
        hls.on(Hls.Events.ERROR, (event, data) => {
          if (data?.fatal) {
            cleanup()
            reject(new Error('视频加载失败'))
          }
        })
        hls.loadSource(url)
        hls.attachMedia(document.createElement('video'))
      })
    },

    // Format seconds to HH:MM:SS
    formatDurationHMS(seconds) {
      const total = Math.round(seconds)
      const hrs = Math.floor(total / 3600)
      const mins = Math.floor((total % 3600) / 60)
      const secs = total % 60
      return [hrs, mins, secs].map(n => String(n).padStart(2, '0')).join(':')
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

.list-header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.select-all-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.85em;
  color: var(--admin-text-muted);
  cursor: pointer;
  user-select: none;
}

.select-all-label input {
  cursor: pointer;
}

.video-select {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.video-select input {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.video-item.selected {
  border-color: var(--admin-primary-border);
  background: var(--admin-primary-soft, var(--admin-surface-3));
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

/* Pagination */
.pagination {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 6px;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid var(--admin-border);
}

.page-btn {
  min-width: 36px;
  padding: 6px 10px;
  font-size: 13px;
  color: var(--admin-text);
  background: var(--admin-surface);
  border: 1px solid var(--admin-border);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.page-btn:hover:not(:disabled) {
  border-color: var(--admin-primary);
  color: var(--admin-primary);
}

.page-btn.active {
  background: var(--admin-primary);
  border-color: var(--admin-primary);
  color: #fff;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  margin-left: 8px;
  font-size: 13px;
  color: var(--admin-text-faint);
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

/* Duration input with auto-detect button */
.duration-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.duration-row .form-input {
  flex: 1;
}

.duration-row .btn {
  white-space: nowrap;
  flex-shrink: 0;
}

/* Cover image preview in modals */
.image-preview {
  margin-top: 10px;
}

.image-preview img {
  max-width: 160px;
  max-height: 90px;
  object-fit: cover;
  border-radius: var(--admin-radius-sm);
  border: 1px solid var(--admin-border-strong);
  background: var(--admin-surface-3);
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
