<template>
  <div class="category-picker" :class="{ open: expanded }">
    <!-- Selected value / trigger -->
    <button type="button" class="picker-trigger" @click="expanded = !expanded">
      <span class="trigger-value" :class="{ placeholder: !modelValue }">
        {{ modelValue || '点击展开选择分类' }}
      </span>
      <span class="trigger-arrow"><AppIcon name="chevron-down" :size="18" /></span>
    </button>

    <!-- Expandable panel -->
    <transition name="picker">
      <div v-if="expanded" class="picker-panel">
        <div class="picker-search">
          <AppIcon name="search" :size="16" />
          <input
            v-model="keyword"
            type="text"
            class="picker-search-input"
            placeholder="搜索或输入自定义分类..."
            @keyup.enter="applyCustom"
          />
          <button
            v-if="keyword.trim()"
            type="button"
            class="picker-custom-btn"
            @click="applyCustom"
          >
            使用「{{ keyword.trim() }}」
          </button>
        </div>

        <div class="picker-groups">
          <div
            v-for="group in filteredGroups"
            :key="group.key"
            class="picker-group"
          >
            <button
              type="button"
              class="group-head"
              @click="toggleGroup(group.key)"
            >
              <span class="group-name">
                <span class="group-dot"></span>
                {{ group.label }}
                <span class="group-count">{{ group.subcategories.length }}</span>
              </span>
              <span class="group-arrow" :class="{ open: openGroups.includes(group.key) }">
                <AppIcon name="chevron-down" :size="16" />
              </span>
            </button>

            <transition name="group">
              <div v-if="openGroups.includes(group.key)" class="group-body">
                <button
                  v-for="sub in group.subcategories"
                  :key="sub"
                  type="button"
                  class="sub-chip"
                  :class="{ selected: modelValue === sub }"
                  @click="select(sub)"
                >
                  <AppIcon v-if="modelValue === sub" name="check" :size="14" />
                  {{ sub }}
                </button>
                <span v-if="group.subcategories.length === 0" class="group-empty">
                  该导航分类暂无绑定分类
                </span>
              </div>
            </transition>
          </div>

          <div v-if="filteredGroups.length === 0" class="picker-empty">
            未找到匹配的分类，可直接输入自定义分类
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script>
import AppIcon from '@/components/AppIcon.vue'
import { getNavCategories } from '@/utils/navCategoryManager'

export default {
  name: 'CategoryPicker',
  components: { AppIcon },
  props: {
    modelValue: {
      type: String,
      default: ''
    }
  },
  emits: ['update:modelValue'],
  data() {
    return {
      expanded: false,
      keyword: '',
      openGroups: [],
      groups: []
    }
  },
  computed: {
    filteredGroups() {
      const kw = this.keyword.trim().toLowerCase()
      if (!kw) return this.groups
      return this.groups
        .map(g => ({
          ...g,
          subcategories: g.subcategories.filter(s => s.toLowerCase().includes(kw))
        }))
        .filter(g => g.subcategories.length > 0 || g.label.toLowerCase().includes(kw))
    }
  },
  mounted() {
    this.loadGroups()
  },
  methods: {
    loadGroups() {
      const cats = getNavCategories() || []
      this.groups = cats.map(c => ({
        key: c.key,
        label: c.label,
        subcategories: Array.isArray(c.subcategories) ? c.subcategories : []
      }))
      // Expand the group that contains the current value, otherwise the first group
      const owner = this.groups.find(g => g.subcategories.includes(this.modelValue))
      if (owner) {
        this.openGroups = [owner.key]
      } else if (this.groups.length > 0) {
        this.openGroups = [this.groups[0].key]
      }
    },
    toggleGroup(key) {
      const idx = this.openGroups.indexOf(key)
      if (idx === -1) {
        this.openGroups.push(key)
      } else {
        this.openGroups.splice(idx, 1)
      }
    },
    select(value) {
      this.$emit('update:modelValue', value)
      this.expanded = false
      this.keyword = ''
    },
    applyCustom() {
      const value = this.keyword.trim()
      if (!value) return
      this.select(value)
    }
  }
}
</script>

<style scoped>
.category-picker {
  position: relative;
}

.picker-trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  width: 100%;
  padding: 10px 15px;
  background: var(--admin-surface);
  border: 1px solid var(--admin-border-strong);
  border-radius: var(--admin-radius-sm);
  color: var(--admin-text);
  font-size: 0.9em;
  cursor: pointer;
  transition: all 0.2s;
}

.picker-trigger:hover {
  border-color: var(--admin-primary-border);
}

.category-picker.open .picker-trigger {
  border-color: var(--admin-primary);
  box-shadow: 0 0 0 3px var(--admin-primary-soft);
}

.trigger-value {
  flex: 1;
  text-align: left;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.trigger-value.placeholder {
  color: var(--admin-text-faint);
}

.trigger-arrow {
  display: inline-flex;
  color: var(--admin-text-muted);
  transition: transform 0.2s;
}

.category-picker.open .trigger-arrow {
  transform: rotate(180deg);
}

.picker-panel {
  position: absolute;
  z-index: 60;
  top: calc(100% + 6px);
  left: 0;
  right: 0;
  background: var(--admin-surface);
  border: 1px solid var(--admin-border);
  border-radius: var(--admin-radius);
  box-shadow: var(--admin-shadow-lg);
  overflow: hidden;
}

.picker-search {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-bottom: 1px solid var(--admin-border);
  color: var(--admin-text-muted);
}

.picker-search-input {
  flex: 1;
  border: none;
  background: transparent;
  color: var(--admin-text);
  font-size: 0.9em;
  outline: none;
}

.picker-search-input::placeholder {
  color: var(--admin-text-faint);
}

.picker-custom-btn {
  padding: 4px 10px;
  border: 1px solid var(--admin-primary-border);
  background: var(--admin-primary-soft);
  color: var(--admin-primary-dark);
  border-radius: 12px;
  font-size: 0.78em;
  cursor: pointer;
  white-space: nowrap;
}

.picker-groups {
  max-height: 260px;
  overflow-y: auto;
  padding: 6px;
}

.picker-group {
  border-radius: var(--admin-radius-sm);
}

.group-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 9px 10px;
  background: transparent;
  border: none;
  border-radius: var(--admin-radius-sm);
  cursor: pointer;
  color: var(--admin-text);
}

.group-head:hover {
  background: var(--admin-surface-2);
}

.group-name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 0.9em;
}

.group-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--admin-primary), var(--admin-accent));
}

.group-count {
  padding: 1px 7px;
  background: var(--admin-surface-3);
  border-radius: 10px;
  font-size: 0.75em;
  font-weight: 600;
  color: var(--admin-text-muted);
}

.group-arrow {
  display: inline-flex;
  color: var(--admin-text-faint);
  transition: transform 0.2s;
}

.group-arrow.open {
  transform: rotate(180deg);
}

.group-body {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 6px 10px 12px;
}

.sub-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 5px 12px;
  background: var(--admin-surface-2);
  border: 1px solid var(--admin-border);
  border-radius: 14px;
  font-size: 0.82em;
  color: var(--admin-text);
  cursor: pointer;
  transition: all 0.15s;
}

.sub-chip:hover {
  border-color: var(--admin-primary-border);
  color: var(--admin-primary-dark);
}

.sub-chip.selected {
  background: var(--admin-primary);
  border-color: var(--admin-primary);
  color: #fff;
}

.group-empty,
.picker-empty {
  padding: 8px 10px;
  font-size: 0.8em;
  color: var(--admin-text-faint);
}

/* transitions */
.picker-enter-active,
.picker-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.picker-enter-from,
.picker-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

.group-enter-active,
.group-leave-active {
  transition: opacity 0.15s ease;
}

.group-enter-from,
.group-leave-to {
  opacity: 0;
}
</style>
