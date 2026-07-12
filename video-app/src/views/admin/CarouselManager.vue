<template>
  <div class="carousel-manager-page">
    <!-- Intro / help -->
    <div class="cm-intro">
      <AppIcon name="image" :size="18" />
      <p>
        在这里配置首页轮播图。你可以单独添加图片，也可以选择已有视频显示在轮播图。
        轮播图只会展示你在这里配置的内容，新增视频不会自动出现在轮播图，只会显示在它所属的分类里。
      </p>
    </div>

    <div class="cm-grid">
      <!-- Current carousel selection -->
      <section class="tab-content">
        <div class="list-header">
          <h3>
            <AppIcon name="image" :size="18" />
            当前轮播图
          </h3>
          <span class="list-count">{{ carouselList.length }} 个视频</span>
        </div>

        <div v-if="loadingCarousel" class="loading-state">
          <div class="loading-spinner"></div>
          <p>加载中...</p>
        </div>

        <div v-else class="videos-list">
          <div
            v-for="(video, index) in carouselList"
            :key="video._uid"
            class="video-item"
          >
            <span class="order-badge">{{ index + 1 }}</span>
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
              <AppIcon :name="video.item_type === 'image' ? 'image' : 'film'" :size="20" />
            </div>
            <div class="video-info">
              <span class="video-title">{{ video.video_title || (video.item_type === 'image' ? '图片' : '未命名') }}</span>
              <span class="video-meta">
                <span v-if="video.item_type === 'image'" class="meta-tag category">图片</span>
                <template v-else>
                  <span class="meta-tag">ID: {{ video.video_id }}</span>
                  <span class="meta-tag category">{{ video.video_category || '未分类' }}</span>
                </template>
              </span>
            </div>
            <div class="video-actions">
              <button
                class="btn btn-secondary btn-sm"
                :disabled="index === 0"
                title="上移"
                @click="moveUp(index)"
              >
                <AppIcon name="arrow-up" :size="14" />
              </button>
              <button
                class="btn btn-secondary btn-sm"
                :disabled="index === carouselList.length - 1"
                title="下移"
                @click="moveDown(index)"
              >
                <AppIcon name="arrow-down" :size="14" />
              </button>
              <button class="btn btn-danger btn-sm" title="移除" @click="removeFromCarousel(video)">
                <AppIcon name="trash" :size="14" />
              </button>
            </div>
          </div>

          <div v-if="carouselList.length === 0" class="empty-state">
            <AppIcon name="image" :size="40" />
            <p>还没有配置轮播图，添加图片或从右侧选择视频。</p>
          </div>
        </div>

        <div class="cm-actions">
          <button class="btn btn-secondary" :disabled="saving" @click="loadCarousel">
            <AppIcon name="refresh" :size="16" /> 重新加载
          </button>
          <button class="btn btn-primary" :disabled="saving" @click="saveCarousel">
            <AppIcon name="check" :size="16" /> {{ saving ? '保存中...' : '保存轮播图' }}
          </button>
        </div>
      </section>

      <!-- Video / image picker -->
      <section class="tab-content">
        <div class="list-header">
          <h3>
            <AppIcon name="image" :size="18" />
            添加图片
          </h3>
        </div>

        <div class="cm-image-form">
          <label class="cm-field">
            <span class="cm-label">图片地址 <em>*</em></span>
            <input
              v-model="imageForm.image_url"
              type="text"
              placeholder="https://example.com/banner.jpg 或点击下方按钮上传"
              class="cm-input"
            />
          </label>
          <div class="cm-upload-row">
            <input
              ref="imageFileInput"
              type="file"
              accept="image/*"
              class="cm-file-hidden"
              @change="onImageFileSelected"
            />
            <button
              class="btn btn-secondary"
              :disabled="uploading"
              @click="triggerImageUpload"
            >
              <AppIcon name="image" :size="16" />
              {{ uploading ? '上传中...' : '上传本地图片' }}
            </button>
            <span class="cm-upload-hint">支持 png/jpg/gif/webp，最大 10MB</span>
          </div>
          <div class="cm-field-row">
            <label class="cm-field">
              <span class="cm-label">标题（可选）</span>
              <input
                v-model="imageForm.title"
                type="text"
                placeholder="轮播图标题"
                class="cm-input"
              />
            </label>
            <label class="cm-field">
              <span class="cm-label">跳转链接（可选）</span>
              <input
                v-model="imageForm.link_url"
                type="text"
                placeholder="https://... 点击图片时打开"
                class="cm-input"
              />
            </label>
          </div>
          <div
            v-if="imageForm.image_url"
            class="cm-image-preview"
          >
            <img
              :src="formatImageUrl(imageForm.image_url)"
              alt="预览"
              referrerpolicy="no-referrer"
              @error="handleImageError"
            />
          </div>
          <div class="cm-image-actions">
            <button class="btn btn-primary" @click="addImageToCarousel">
              <AppIcon name="plus" :size="16" /> 添加图片到轮播图
            </button>
          </div>
        </div>

        <div class="list-header cm-picker-header">
          <h3>
            <AppIcon name="film" :size="18" />
            添加视频
          </h3>
        </div>

        <div class="cm-toolbar">
          <div class="search-box">
            <AppIcon name="search" :size="18" class="search-icon" />
            <input
              v-model="searchKeyword"
              type="text"
              placeholder="搜索视频标题..."
              class="search-input"
              @keyup.enter="searchVideos"
            />
          </div>
          <div class="filter-box">
            <AppIcon name="filter" :size="16" class="filter-icon" />
            <select v-model="filterCategory" class="select-input" @change="searchVideos">
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

        <div v-if="loadingResults" class="loading-state">
          <div class="loading-spinner"></div>
          <p>加载中...</p>
        </div>

        <div v-else class="videos-list">
          <div
            v-for="video in searchResults"
            :key="video.video_id"
            class="video-item"
          >
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
              </span>
            </div>
            <div class="video-actions">
              <button
                v-if="isInCarousel(video.video_id)"
                class="btn btn-secondary btn-sm"
                disabled
              >
                <AppIcon name="check" :size="14" /> 已添加
              </button>
              <button
                v-else
                class="btn btn-primary btn-sm"
                @click="addToCarousel(video)"
              >
                <AppIcon name="plus" :size="14" /> 添加
              </button>
            </div>
          </div>

          <div v-if="searchResults.length === 0" class="empty-state">
            <AppIcon name="film" :size="40" />
            <p>暂无视频，试试搜索或切换分类。</p>
          </div>
        </div>
      </section>
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

export default {
  name: 'CarouselManager',
  components: { AppIcon },
  data() {
    return {
      navGroups: [],

      // Current carousel selection (ordered list of video objects)
      carouselList: [],
      loadingCarousel: false,
      saving: false,

      // Video picker
      searchResults: [],
      loadingResults: false,
      searchKeyword: '',
      filterCategory: '',

      // Standalone image form
      imageForm: {
        image_url: '',
        title: '',
        link_url: ''
      },

      // Local image upload state
      uploading: false,

      // Incrementing id used to give every carousel entry a stable v-for key
      uidCounter: 0,

      // Toast
      toastMessage: '',
      toastType: ''
    }
  },
  mounted() {
    this.loadNavGroups()
    this.refreshNavGroups()
    this.loadCarousel()
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
      try {
        await fetchNavCategories()
        this.loadNavGroups()
      } catch (e) {
        console.error('Load nav categories error:', e)
      }
    },

    async loadCarousel() {
      this.loadingCarousel = true
      try {
        const result = await videoApi.getCarousel()
        const items = extractArrayData(result)
        this.carouselList = items.map(item => this.normalizeItem(item))
      } catch (e) {
        console.error('Load carousel error:', e)
        this.showToast('加载轮播图失败', 'error')
      } finally {
        this.loadingCarousel = false
      }
    },

    // Give every carousel entry a stable local uid and a consistent shape.
    normalizeItem(item) {
      const isImage = item.item_type === 'image'
      return {
        _uid: `cm-${this.uidCounter++}`,
        item_type: isImage ? 'image' : 'video',
        video_id: isImage ? null : item.video_id,
        video_title: item.video_title || '',
        video_image: item.video_image || '',
        video_category: item.video_category || '',
        image_url: isImage ? (item.video_image || item.image_url || '') : '',
        link_url: item.link_url || ''
      }
    },

    async searchVideos() {
      this.loadingResults = true
      try {
        let result
        if (this.searchKeyword) {
          result = await videoApi.searchVideos(this.searchKeyword, 50)
          let videos = extractArrayData(result)
          if (this.filterCategory) {
            videos = videos.filter(v => v.video_category === this.filterCategory)
          }
          this.searchResults = videos
        } else if (this.filterCategory) {
          result = await videoApi.getCategoryVideosAdmin(this.filterCategory, 50)
          this.searchResults = extractArrayData(result)
        } else {
          result = await videoApi.getVideos({ limit: 50 })
          this.searchResults = extractArrayData(result)
        }
      } catch (e) {
        console.error('Search videos error:', e)
        this.showToast('加载视频失败', 'error')
      } finally {
        this.loadingResults = false
      }
    },

    isInCarousel(videoId) {
      return this.carouselList.some(v => v.item_type === 'video' && v.video_id === videoId)
    },

    addToCarousel(video) {
      if (this.isInCarousel(video.video_id)) return
      this.carouselList.push(this.normalizeItem({ ...video, item_type: 'video' }))
      this.showToast('已添加到轮播图，记得点击保存', 'info')
    },

    triggerImageUpload() {
      if (this.uploading) return
      const input = this.$refs.imageFileInput
      if (input) input.click()
    },

    async onImageFileSelected(event) {
      const input = event.target
      const file = input && input.files && input.files[0]
      if (!file) return

      if (!file.type || !file.type.startsWith('image/')) {
        this.showToast('请选择图片文件', 'error')
        input.value = ''
        return
      }
      // 10MB limit, matches the backend MAX_CONTENT_LENGTH
      if (file.size > 10 * 1024 * 1024) {
        this.showToast('图片过大，最大 10MB', 'error')
        input.value = ''
        return
      }

      this.uploading = true
      try {
        const result = await videoApi.uploadImage(file)
        const url = result && result.data && result.data.url
        if (url) {
          this.imageForm.image_url = url
          this.showToast('图片上传成功，点击“添加图片到轮播图”', 'success')
        } else {
          this.showToast('上传失败：未返回图片地址', 'error')
        }
      } catch (e) {
        console.error('Upload image error:', e)
        this.showToast('图片上传失败', 'error')
      } finally {
        this.uploading = false
        // Allow selecting the same file again
        input.value = ''
      }
    },

    addImageToCarousel() {
      const imageUrl = (this.imageForm.image_url || '').trim()
      if (!imageUrl) {
        this.showToast('请填写图片地址', 'error')
        return
      }
      this.carouselList.push(this.normalizeItem({
        item_type: 'image',
        video_image: imageUrl,
        video_title: (this.imageForm.title || '').trim(),
        link_url: (this.imageForm.link_url || '').trim()
      }))
      this.imageForm = { image_url: '', title: '', link_url: '' }
      this.showToast('已添加图片到轮播图，记得点击保存', 'info')
    },

    removeFromCarousel(video) {
      this.carouselList = this.carouselList.filter(v => v._uid !== video._uid)
    },

    moveUp(index) {
      if (index <= 0) return
      const list = this.carouselList
      ;[list[index - 1], list[index]] = [list[index], list[index - 1]]
    },

    moveDown(index) {
      const list = this.carouselList
      if (index >= list.length - 1) return
      ;[list[index + 1], list[index]] = [list[index], list[index + 1]]
    },

    async saveCarousel() {
      this.saving = true
      try {
        const items = this.carouselList.map(v => {
          if (v.item_type === 'image') {
            return {
              item_type: 'image',
              image_url: v.image_url || v.video_image,
              title: v.video_title || '',
              link_url: v.link_url || ''
            }
          }
          return { item_type: 'video', video_id: v.video_id }
        })
        await videoApi.saveCarouselItems(items)
        // Clear API cache so the home page reflects the new carousel immediately
        videoApi.clearCache()
        this.showToast('轮播图配置已保存', 'success')
      } catch (e) {
        console.error('Save carousel error:', e)
        this.showToast('保存轮播图失败', 'error')
      } finally {
        this.saving = false
      }
    },

    formatImageUrl(url) {
      return formatImageUrl(url)
    },

    handleImageError(e) {
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
.carousel-manager-page {
  max-width: 1200px;
}

.cm-intro {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 14px 18px;
  margin-bottom: 20px;
  background: var(--admin-primary-soft);
  border: 1px solid var(--admin-primary-border);
  border-radius: var(--admin-radius-sm);
  color: var(--admin-primary-dark);
}

.cm-intro p {
  margin: 0;
  font-size: 0.9em;
  line-height: 1.5;
}

.cm-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  align-items: start;
}

/* Toolbar */
.cm-toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}

.cm-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 18px;
  padding-top: 14px;
  border-top: 1px solid var(--admin-border);
}

/* Standalone image form */
.cm-image-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 20px;
}

.cm-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1;
  min-width: 0;
}

.cm-field-row {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.cm-label {
  font-size: 0.82em;
  color: var(--admin-text-muted);
}

.cm-label em {
  color: var(--admin-danger);
  font-style: normal;
}

.cm-input {
  padding: 10px 14px;
  background: var(--admin-surface);
  border: 1px solid var(--admin-border-strong);
  border-radius: var(--admin-radius-sm);
  color: var(--admin-text);
  font-size: 0.9em;
  width: 100%;
}

.cm-input:focus {
  outline: none;
  border-color: var(--admin-primary);
  box-shadow: 0 0 0 3px var(--admin-primary-soft);
}

.cm-image-preview {
  position: relative;
  width: 100%;
  padding-top: 40%;
  border-radius: var(--admin-radius-sm);
  overflow: hidden;
  background: var(--admin-surface-3);
}

.cm-image-preview img {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cm-image-actions {
  display: flex;
  justify-content: flex-end;
}

.cm-upload-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.cm-file-hidden {
  display: none;
}

.cm-upload-hint {
  font-size: 0.78em;
  color: var(--admin-text-muted);
}

.cm-picker-header {
  margin-top: 8px;
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
  min-width: 180px;
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
.select-input:focus {
  outline: none;
  border-color: var(--admin-primary);
  box-shadow: 0 0 0 3px var(--admin-primary-soft);
}

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
  gap: 12px;
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

.order-badge {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: var(--admin-primary-soft);
  color: var(--admin-primary-dark);
  font-size: 0.8em;
  font-weight: 600;
}

.video-thumb {
  width: 80px;
  height: 46px;
  object-fit: cover;
  border-radius: 6px;
  background: var(--admin-surface-3);
  flex-shrink: 0;
}

.video-thumb-placeholder {
  width: 80px;
  height: 46px;
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
  gap: 6px;
  flex-shrink: 0;
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

/* Responsive */
@media (max-width: 992px) {
  .cm-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .cm-toolbar {
    flex-direction: column;
    align-items: stretch;
  }

  .search-input,
  .select-input {
    min-width: 0;
    width: 100%;
  }

  .tab-content {
    padding: 15px;
  }

  .video-item {
    flex-wrap: wrap;
  }
}
</style>
