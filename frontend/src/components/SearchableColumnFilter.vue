<template>
  <div class="searchable-filter-inline" ref="wrapperRef">
    <div class="input-wrapper">
      <t-input
        v-model="searchText"
        placeholder="筛选 UP 主"
        :disabled="loading"
        @focus="openDropdown"
        @input="handleSearch"
        @keydown="handleKeydown"
        size="small"
        ref="inputRef"
      >
        <template #prefix-icon>
          <t-icon name="search" size="14px" />
        </template>
      </t-input>
      <span
        v-if="localValue.length > 0"
        class="clear-icon"
        @click.stop="clearFilter"
      >
        ×
      </span>
    </div>

    <transition name="dropdown">
      <div v-if="isOpen" class="filter-dropdown">
        <div class="filter-options" ref="optionsRef">
          <div v-if="loading" class="filter-loading">
            <t-icon name="loading" size="20px" class="t-icon-loading-spin" />
            <span>搜索中...</span>
          </div>

          <div v-else-if="filteredOptions.length === 0" class="filter-empty">
            <t-icon name="search-off" size="20px" />
            <span>无匹配数据</span>
          </div>

          <div
            v-else
            class="option-item"
            v-for="(option, index) in filteredOptions"
            :key="option.value"
            :class="{ 'option-item--selected': localValue.includes(option.value), 'option-item--hovered': hoveredIndex === index }"
            @click="selectOption(option.value)"
            @mouseenter="hoveredIndex = index"
          >
            <t-checkbox :checked="localValue.includes(option.value)" />
            <span class="option-label" v-html="highlightMatch(option.label)"></span>
          </div>
        </div>

        <div class="filter-footer" v-if="filteredOptions.length > 0">
          <span class="selected-count" v-if="localValue.length > 0">
            已选择 {{ localValue.length }} 个
          </span>
          <div class="filter-actions">
            <t-button size="small" variant="outline" @click="clearFilter">清空</t-button>
            <t-button size="small" theme="primary" @click="confirmFilter">确定</t-button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { Icon as TIcon } from 'tdesign-vue-next'
import { http } from '../api/http'

const props = defineProps({
  value: {
    type: Array,
    default: () => []
  },
  options: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['filterChange'])

const isOpen = ref(false)
const searchText = ref('')
const localValue = ref([...props.value])
const loading = ref(false)
const hoveredIndex = ref(-1)

const inputRef = ref(null)
const wrapperRef = ref(null)
const optionsRef = ref(null)

const allOptions = ref([])

const fetchOptions = async () => {
  try {
    loading.value = true
    const response = await http.get('/api/files')
    const fileUps = (response.data.files || []).map(f => f.up).filter(Boolean)
    const upList = response.data.upList || []
    const ups = new Set([...upList, ...fileUps])
    allOptions.value = Array.from(ups).map(up => ({
      label: up,
      value: up
    })).sort((a, b) => a.label.localeCompare(b.label))
  } catch (e) {
    console.error('获取UP主列表失败:', e)
    allOptions.value = props.options
  } finally {
    loading.value = false
  }
}

const filteredOptions = computed(() => {
  const query = searchText.value.trim().toLowerCase()
  if (!query) return allOptions.value
  return allOptions.value.filter(opt =>
    opt.label.toLowerCase().includes(query)
  )
})

const highlightMatch = (text) => {
  if (!searchText.value) return text
  const query = searchText.value.trim()
  if (!query) return text
  const escaped = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  const regex = new RegExp(`(${escaped})`, 'gi')
  return String(text).replace(regex, '<span class="highlight-match">$1</span>')
}

let searchTimer = null
const handleSearch = () => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    hoveredIndex.value = -1
  }, 300)
}

const selectOption = (value) => {
  const index = localValue.value.indexOf(value)
  if (index >= 0) {
    localValue.value.splice(index, 1)
  } else {
    localValue.value.push(value)
  }
  hoveredIndex.value = -1
}

const clearFilter = () => {
  localValue.value = []
  searchText.value = ''
  emit('filterChange', { up: [] })
  isOpen.value = false
}

const confirmFilter = () => {
  emit('filterChange', { up: [...localValue.value] })
  isOpen.value = false
  nextTick(() => {
    inputRef.value?.blur()
  })
}

const openDropdown = async () => {
  if (!isOpen.value) {
    isOpen.value = true
    searchText.value = ''
    hoveredIndex.value = -1
    if (allOptions.value.length === 0) {
      await fetchOptions()
    }
  }
}

const closeDropdown = () => {
  isOpen.value = false
  searchText.value = ''
}

const handleClickOutside = (e) => {
  if (wrapperRef.value && !wrapperRef.value.contains(e.target)) {
    if (localValue.value.length > 0 && searchText.value.trim() === '') {
      emit('filterChange', { up: [...localValue.value] })
    }
    closeDropdown()
  }
}

const handleKeydown = (e) => {
  if (!isOpen.value) return

  const options = filteredOptions.value
  if (options.length === 0) return

  switch (e.key) {
    case 'ArrowDown':
      e.preventDefault()
      hoveredIndex.value = Math.min(hoveredIndex.value + 1, options.length - 1)
      scrollToHovered()
      break
    case 'ArrowUp':
      e.preventDefault()
      hoveredIndex.value = Math.max(hoveredIndex.value - 1, 0)
      scrollToHovered()
      break
    case 'Enter':
      e.preventDefault()
      if (hoveredIndex.value >= 0 && hoveredIndex.value < options.length) {
        selectOption(options[hoveredIndex.value].value)
      } else if (searchText.value.trim() !== '') {
        confirmFilter()
      }
      break
    case 'Escape':
      if (localValue.value.length > 0 && searchText.value.trim() === '') {
        emit('filterChange', { up: [...localValue.value] })
      }
      closeDropdown()
      inputRef.value?.blur()
      break
  }
}

const scrollToHovered = () => {
  if (hoveredIndex.value < 0 || !optionsRef.value) return
  const optionsEl = optionsRef.value
  const items = optionsEl.querySelectorAll('.option-item')
  if (items[hoveredIndex.value]) {
    items[hoveredIndex.value].scrollIntoView({ block: 'nearest' })
  }
}

watch(() => props.value, (newVal) => {
  localValue.value = [...(newVal || [])]
})

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  document.addEventListener('keydown', handleKeydown)
  fetchOptions()
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  document.removeEventListener('keydown', handleKeydown)
  if (searchTimer) clearTimeout(searchTimer)
})
</script>

<style scoped>
.searchable-filter-inline {
  position: relative;
  width: 100%;
  min-width: 140px;
}

.input-wrapper {
  display: flex;
  align-items: center;
  gap: 4px;
}

.input-wrapper :deep(.t-input) {
  width: 100%;
  cursor: text;
}

.input-wrapper :deep(.t-input__inner) {
  cursor: text;
}

.clear-icon {
  cursor: pointer;
  font-size: 18px;
  color: var(--td-text-color-secondary);
  line-height: 1;
  margin-left: -20px;
  z-index: 1;
}

.clear-icon:hover {
  color: var(--td-brand-color);
}

.filter-dropdown {
  position: fixed;
  min-width: 260px;
  max-width: 320px;
  background: var(--td-bg-color-container);
  border: 1px solid var(--td-component-border);
  border-radius: var(--td-radius-medium);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 9999;
  overflow: hidden;
}

.dropdown-enter-active,
.dropdown-leave-active {
  transition: opacity 0.15s ease;
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
}

.filter-options {
  max-height: 220px;
  overflow-y: auto;
}

.filter-loading,
.filter-empty {
  padding: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: var(--td-text-color-secondary);
}

.option-item {
  padding: 10px 12px;
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  transition: background-color 0.15s;
}

.option-item:hover {
  background-color: var(--td-bg-color-container-hover);
}

.option-item--selected {
  background-color: var(--td-brand-color-light);
}

.option-item--hovered {
  background-color: var(--td-bg-color-container-hover);
}

.option-label {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

:deep(.highlight-match) {
  color: var(--td-brand-color);
  font-weight: bold;
  background-color: var(--td-brand-color-light);
}

.filter-footer {
  padding: 10px 12px;
  border-top: 1px solid var(--td-component-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  background: var(--td-bg-color-secondary-container);
}

.filter-actions {
  display: flex;
  gap: 8px;
}

.selected-count {
  font-size: 12px;
  color: var(--td-text-color-secondary);
}

.t-icon-loading-spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
