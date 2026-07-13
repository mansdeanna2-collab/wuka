<template>
  <div class="video-collection-page">
    <div class="page-intro">
      <h3><AppIcon name="download" :size="20" /> 视频采集</h3>
      <p class="intro-desc">从采集源检查并抓取最新视频到本地数据库。支持通用采集源与 Hanime1 裏番采集。</p>
    </div>

    <!-- Collection Controls -->
    <div class="panel collection-controls">
      <h4><AppIcon name="rocket" :size="18" /> 后台采集</h4>
      <div class="control-row">
        <div class="control-group">
          <label>采集分类</label>
          <select v-model="collectTypeId" class="select-input">
            <option value="">全部分类</option>
            <option v-for="cat in sourceCategories" :key="cat.type_id" :value="cat.type_id">
              {{ cat.type_name }}
            </option>
          </select>
        </div>
        <div class="control-group">
          <label>时间范围</label>
          <select v-model="collectHours" class="select-input">
            <option value="24">24小时内</option>
            <option value="48">48小时内</option>
            <option value="72">72小时内</option>
            <option value="168">7天内</option>
          </select>
        </div>
        <div class="control-group">
          <label>采集页数</label>
          <select v-model="collectMaxPages" class="select-input">
            <option value="1">1页</option>
            <option value="3">3页</option>
            <option value="5">5页</option>
            <option value="10">10页</option>
            <option value="20">20页</option>
          </select>
        </div>
        <div class="control-group checkbox-group">
          <label>
            <input type="checkbox" v-model="collectSkipDuplicates" />
            跳过已有视频
          </label>
        </div>
        <button
          class="btn btn-primary"
          @click="startCollection"
          :disabled="collectingVideos"
        >
          {{ collectingVideos ? '采集中...' : '开始采集' }}
        </button>
      </div>

      <div v-if="collectionResult" class="collection-result">
        <h5>采集结果</h5>
        <div class="result-summary">
          <span class="highlight">成功采集: {{ collectionResult.collected_count }} 个</span>
          <span>跳过无效: {{ collectionResult.skipped_count }} 个</span>
          <span>已存在: {{ collectionResult.duplicate_count }} 个</span>
          <span>处理页数: {{ collectionResult.pages_processed }} 页</span>
        </div>
      </div>
    </div>

    <!-- Hanime1 Collection -->
    <div class="panel collection-controls">
      <h4><AppIcon name="download" :size="18" /> Hanime1 裏番采集</h4>
      <p class="intro-desc">
        从 hanime1.me 采集裏番(里番)动漫:自动解析最高画质播放地址、标签、观看次数与上传日期,默认归类到「里番动漫」并入库。同名视频只替换图片/视频链接,不新增重复数据。
      </p>
      <div class="control-row">
        <div class="control-group">
          <label>采集分类 (genre)</label>
          <input v-model="hanimeGenre" class="select-input" placeholder="裏番" />
        </div>
        <div class="control-group">
          <label>入库分类</label>
          <input v-model="hanimeCategory" class="select-input" placeholder="里番动漫" />
        </div>
        <div class="control-group">
          <label>采集页数</label>
          <select v-model="hanimeMaxPages" class="select-input">
            <option value="1">1页</option>
            <option value="2">2页</option>
            <option value="3">3页</option>
            <option value="5">5页</option>
            <option value="10">10页</option>
          </select>
        </div>
        <div class="control-group">
          <label>请求间隔(秒)</label>
          <select v-model="hanimeDelay" class="select-input">
            <option value="0.5">0.5秒</option>
            <option value="1">1秒</option>
            <option value="2">2秒</option>
            <option value="3">3秒</option>
          </select>
        </div>
        <div class="control-group checkbox-group">
          <label>
            <input type="checkbox" v-model="hanimeSkipDuplicates" />
            重复名称只替换链接
          </label>
        </div>
        <button
          class="btn btn-primary"
          @click="startHanimeCollection"
          :disabled="collectingHanime"
        >
          {{ collectingHanime ? '采集中...' : '开始采集' }}
        </button>
      </div>

      <div v-if="hanimeResult" class="collection-result">
        <h5>采集结果</h5>
        <div class="result-summary">
          <span class="highlight">成功采集: {{ hanimeResult.collected_count }} 个</span>
          <span>更新链接: {{ hanimeResult.updated_count || 0 }} 个</span>
          <span>跳过无效: {{ hanimeResult.skipped_count }} 个</span>
          <span>处理页数: {{ hanimeResult.pages_processed }} 页</span>
        </div>

        <div
          v-if="hanimeResult.collected_videos && hanimeResult.collected_videos.length > 0"
          class="new-videos-list"
        >
          <h5>本次采集预览</h5>
          <div
            v-for="video in hanimeResult.collected_videos"
            :key="video.video_id"
            class="video-item compact"
          >
            <div class="video-info">
              <span class="video-title">{{ video.video_title }}</span>
              <span class="video-meta">
                {{ video.best_quality ? video.best_quality + 'p' : '—' }}
                | 观看 {{ video.play_count }}
                | {{ video.upload_date || '—' }}
              </span>
              <span v-if="video.tags && video.tags.length" class="video-tags">
                <span
                  v-for="tag in video.tags.slice(0, 8)"
                  :key="tag"
                  class="video-tag-chip"
                >{{ tag }}</span>
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Collection Status -->
    <div class="panel">
      <div class="section-header">
        <h3><AppIcon name="chart" :size="18" /> 采集状态</h3>
        <div class="header-actions">
          <select v-model="collectionHours" class="select-input">
            <option value="24">24小时内</option>
            <option value="48">48小时内</option>
            <option value="72">72小时内</option>
            <option value="168">7天内</option>
          </select>
          <button class="btn btn-secondary btn-sm" @click="checkNewVideos">
            检查新视频
          </button>
        </div>
      </div>

      <div v-if="loadingCollection" class="loading-state">
        <div class="loading-spinner"></div>
        <p>检查中...</p>
      </div>

      <div v-else-if="collectionStatus" class="collection-info">
        <div class="status-cards">
          <div class="status-card">
            <span class="status-label">数据库总视频</span>
            <span class="status-value">{{ collectionStatus.total_videos || 0 }}</span>
          </div>
          <div class="status-card">
            <span class="status-label">总分类数</span>
            <span class="status-value">{{ collectionStatus.total_categories || 0 }}</span>
          </div>
          <div class="status-card">
            <span class="status-label">最新采集时间</span>
            <span class="status-value small">{{ collectionStatus.latest_collection_time || '无' }}</span>
          </div>
        </div>

        <div v-if="newVideosResult" class="new-videos-section">
          <h4>新视频检查结果</h4>
          <div class="result-summary">
            <span>源站可用: {{ newVideosResult.total_available }} 个</span>
            <span>本次检查: {{ newVideosResult.checked_count }} 个</span>
            <span class="highlight">新视频: {{ newVideosResult.new_count }} 个</span>
            <span>已采集: {{ newVideosResult.already_collected_count }} 个</span>
          </div>

          <div v-if="newVideosResult.new_videos && newVideosResult.new_videos.length > 0" class="new-videos-list">
            <h5>待采集视频预览 (前20个)</h5>
            <div
              v-for="video in newVideosResult.new_videos"
              :key="video.vod_id"
              class="video-item compact"
            >
              <img
                v-if="video.vod_pic"
                :src="formatImageUrl(video.vod_pic)"
                :alt="video.vod_name"
                class="video-thumb small"
                @error="handleImageError"
              />
              <div class="video-info">
                <span class="video-title">{{ video.vod_name }}</span>
                <span class="video-meta">{{ video.type_name }} | {{ video.vod_time }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="empty-state">
        <p>点击"检查新视频"获取采集状态</p>
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
import AppIcon from '@/components/AppIcon.vue'

export default {
  name: 'VideoCollection',
  components: { AppIcon },
  data() {
    return {
      // Collection Status
      collectionHours: 24,
      collectionStatus: null,
      newVideosResult: null,
      loadingCollection: false,

      // Background Collection
      sourceCategories: [],
      collectTypeId: '',
      collectHours: 24,
      collectMaxPages: 1,
      collectSkipDuplicates: true,
      collectingVideos: false,
      collectionResult: null,

      // Hanime1 Collection
      hanimeGenre: '裏番',
      hanimeCategory: '里番动漫',
      hanimeMaxPages: 1,
      hanimeDelay: 1,
      hanimeSkipDuplicates: true,
      collectingHanime: false,
      hanimeResult: null,

      // Toast
      toastMessage: '',
      toastType: ''
    }
  },
  mounted() {
    this.loadSourceCategories()
  },
  methods: {
    // Load source categories from collector API
    async loadSourceCategories() {
      try {
        const result = await videoApi.getSourceCategories()
        this.sourceCategories = extractArrayData(result)
      } catch (e) {
        console.error('Load source categories error:', e)
        // Silently fail - categories are optional for collection
      }
    },

    // Collection Status
    async checkNewVideos() {
      this.loadingCollection = true

      try {
        // First get local collection status
        const statusResult = await videoApi.getCollectionStatus(this.collectionHours)
        this.collectionStatus = statusResult?.data || statusResult

        // Then check for new videos from source
        const newResult = await videoApi.checkNewVideos(this.collectionHours)
        this.newVideosResult = newResult?.data || newResult

        if (this.newVideosResult.new_count > 0) {
          this.showToast(`发现 ${this.newVideosResult.new_count} 个新视频可采集`, 'success')
        } else {
          this.showToast('暂无新视频', 'info')
        }
      } catch (e) {
        console.error('Check new videos error:', e)
        this.showToast('检查新视频失败', 'error')
      } finally {
        this.loadingCollection = false
      }
    },

    // Start background collection
    async startCollection() {
      if (this.collectingVideos) return

      this.collectingVideos = true
      this.collectionResult = null

      try {
        const result = await videoApi.collectVideos({
          type_id: this.collectTypeId || null,
          hours: parseInt(this.collectHours),
          max_pages: parseInt(this.collectMaxPages),
          skip_duplicates: this.collectSkipDuplicates
        })

        this.collectionResult = result?.data || result

        if (this.collectionResult.collected_count > 0) {
          this.showToast(`成功采集 ${this.collectionResult.collected_count} 个视频`, 'success')
          // Refresh status after collection
          this.checkNewVideos()
        } else {
          this.showToast('没有新视频可采集', 'info')
        }
      } catch (e) {
        console.error('Collection error:', e)
        this.showToast('采集失败: ' + (e.userMessage || e.message), 'error')
      } finally {
        this.collectingVideos = false
      }
    },

    // Start Hanime1 collection
    async startHanimeCollection() {
      if (this.collectingHanime) return

      this.collectingHanime = true
      this.hanimeResult = null

      try {
        const result = await videoApi.collectHanime({
          genre: this.hanimeGenre || '裏番',
          category: this.hanimeCategory || '里番动漫',
          max_pages: parseInt(this.hanimeMaxPages),
          delay: parseFloat(this.hanimeDelay),
          skip_duplicates: this.hanimeSkipDuplicates
        })

        this.hanimeResult = result?.data || result

        const collected = this.hanimeResult.collected_count || 0
        const updated = this.hanimeResult.updated_count || 0
        if (collected > 0 || updated > 0) {
          const parts = []
          if (collected > 0) parts.push(`新增 ${collected} 个`)
          if (updated > 0) parts.push(`更新链接 ${updated} 个`)
          this.showToast('采集完成: ' + parts.join('，'), 'success')
        } else {
          this.showToast('没有新视频可采集', 'info')
        }
      } catch (e) {
        console.error('Hanime collection error:', e)
        this.showToast('采集失败: ' + (e.userMessage || e.message), 'error')
      } finally {
        this.collectingHanime = false
      }
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
.video-collection-page {
  max-width: 1200px;
}

.page-intro {
  margin-bottom: 20px;
}

.page-intro h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 6px 0;
  font-size: 1.3em;
  color: var(--admin-text);
}

.intro-desc {
  margin: 0;
  color: var(--admin-text-muted);
  font-size: 0.9em;
}

/* Panels */
.panel {
  background: var(--admin-surface);
  border: 1px solid var(--admin-border);
  border-radius: var(--admin-radius);
  padding: 25px;
  box-shadow: var(--admin-shadow-sm);
  margin-bottom: 25px;
}

/* Section Header */
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-header h3 {
  display: flex;
  align-items: center;
  gap: 8px;
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

/* Form inputs */
.select-input {
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

.select-input:focus {
  outline: none;
  border-color: var(--admin-primary);
  box-shadow: 0 0 0 3px var(--admin-primary-soft);
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

/* Collection Controls */
.collection-controls h4 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 15px 0;
  color: var(--admin-text);
  font-size: 1.1em;
}

.control-row {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  align-items: flex-end;
}

.control-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.control-group label {
  font-size: 0.85em;
  color: var(--admin-text-muted);
}

.control-group.checkbox-group {
  flex-direction: row;
  align-items: center;
}

.control-group.checkbox-group label {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--admin-text);
  cursor: pointer;
}

.control-group.checkbox-group input[type="checkbox"] {
  width: 18px;
  height: 18px;
  accent-color: var(--admin-primary);
}

.collection-result {
  margin-top: 20px;
  padding: 15px;
  background: var(--admin-success-soft);
  border: 1px solid var(--admin-success-border);
  border-radius: var(--admin-radius-sm);
}

.collection-result h5 {
  margin: 0 0 10px 0;
  color: var(--admin-success);
  font-size: 0.95em;
}

.collection-info {
  display: flex;
  flex-direction: column;
  gap: 25px;
}

.status-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 15px;
}

.status-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 20px;
  background: var(--admin-surface-2);
  border: 1px solid var(--admin-border);
  border-radius: var(--admin-radius);
  text-align: center;
}

.status-label {
  font-size: 0.85em;
  color: var(--admin-text-muted);
}

.status-value {
  font-size: 1.8em;
  font-weight: 700;
  color: var(--admin-accent-ink);
}

.status-value.small {
  font-size: 0.9em;
}

.new-videos-section h4 {
  margin: 0 0 15px 0;
  color: var(--admin-text);
  font-size: 1.1em;
}

.new-videos-section h5 {
  margin: 15px 0 10px 0;
  color: var(--admin-text-muted);
  font-size: 0.95em;
}

.result-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  padding: 15px;
  background: var(--admin-surface-2);
  border: 1px solid var(--admin-border);
  border-radius: var(--admin-radius-sm);
  font-size: 0.9em;
  color: var(--admin-text-muted);
}

.result-summary .highlight {
  color: var(--admin-success);
  font-weight: 600;
}

.new-videos-list {
  margin-top: 15px;
  max-height: 400px;
  overflow-y: auto;
}

/* Video Items */
.video-item {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 12px 15px;
  background: var(--admin-surface-2);
  border: 1px solid var(--admin-border);
  border-radius: var(--admin-radius-sm);
  margin-bottom: 10px;
}

.video-item.compact {
  padding: 8px 12px;
}

.video-thumb {
  width: 80px;
  height: 45px;
  object-fit: cover;
  border-radius: 4px;
  background: var(--admin-surface-3);
}

.video-thumb.small {
  width: 60px;
  height: 34px;
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

.video-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin-top: 4px;
}

.video-tag-chip {
  font-size: 0.72em;
  color: var(--admin-text-muted);
  background: var(--admin-surface-3);
  border: 1px solid var(--admin-border);
  border-radius: 10px;
  padding: 1px 8px;
  white-space: nowrap;
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
  .panel {
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

  .video-item {
    flex-wrap: wrap;
  }
}
</style>
