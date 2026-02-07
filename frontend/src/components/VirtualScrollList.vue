<template>
  <div
    ref="containerRef"
    class="virtual-scroll-container"
    :style="containerStyles"
    @scroll="onScroll"
    @wheel="onWheel"
    role="listbox"
    :aria-label="ariaLabel"
    :aria-multiselectable="false"
    tabindex="0"
    @keydown="onKeydown"
  >
    <div
      class="virtual-scroll-content"
      :style="contentStyles"
      role="presentation"
    >
      <div
        v-for="(item, index) in visibleItems"
        :key="getItemKey(item, index)"
        class="virtual-scroll-item"
        :style="getItemStyle(index)"
        role="option"
        :aria-selected="selectedIndex === index"
        :tabindex="selectedIndex === index ? 0 : -1"
        @click="onItemClick(index)"
        @mouseenter="onItemHover(index)"
      >
        <div class="default-item-content">
          {{ getItemText(item) }}
        </div>
      </div>
    </div>

    <div
      v-if="showScrollbar"
      class="virtual-scroll-scrollbar"
      :class="{ 'scrollbar-hover': isScrollbarHovered }"
      @mouseenter="isScrollbarHovered = true"
      @mouseleave="isScrollbarHovered = false"
    >
      <div
        ref="thumbRef"
        class="scrollbar-thumb"
        :style="thumbStyles"
        @mousedown="startDrag"
      />
    </div>

    <div v-if="isDragging" class="drag-overlay" @mousemove="onDrag" @mouseup="stopDrag" @mouseleave="stopDrag" />
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick, shallowRef, toRef } from 'vue'

const props = defineProps({
  items: {
    type: Array,
    default: () => []
  },
  height: {
    type: [String, Number],
    default: '100%'
  },
  minHeight: {
    type: [String, Number],
    default: '0'
  },
  maxHeight: {
    type: [String, Number],
    default: '100%'
  },
  itemHeight: {
    type: Number,
    default: 60
  },
  overscan: {
    type: Number,
    default: 5
  },
  bufferSize: {
    type: Number,
    default: 10
  },
  keyField: {
    type: String,
    default: 'id'
  },
  itemTextField: {
    type: String,
    default: 'title'
  },
  ariaLabel: {
    type: String,
    default: '滚动列表'
  },
  persistScrollKey: {
    type: String,
    default: ''
  },
  selectedIndex: {
    type: Number,
    default: -1
  },
  smoothScroll: {
    type: Boolean,
    default: true
  },
  RTL: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['scroll', 'item-click', 'item-hover', 'scroll-start', 'scroll-end', 'update:selectedIndex'])

const containerRef = ref(null)
const thumbRef = ref(null)
const scrollTop = ref(0)
const containerHeight = ref((() => {
  if (typeof props.height === 'number') return props.height
  if (typeof props.height === 'string') {
    const m = props.height.match(/^\s*(\d+)\s*px\s*$/i)
    if (m) return parseInt(m[1], 10)
  }
  return 200
})())
const isScrollbarHovered = ref(false)
const isDragging = ref(false)
const dragStartY = ref(0)
const dragStartScrollTop = ref(0)
const mounted = ref(false)
const lastScrollPosition = ref(0)
const lastUpdateTime = ref(Date.now())

const selectedIndex = toRef(props, 'selectedIndex')

const itemsList = computed(() => {
  const v = props.items
  if (Array.isArray(v)) return v
  if (v && typeof v === 'object' && Array.isArray(v.value)) return v.value
  return []
})

const contentHeight = computed(() => itemsList.value.length * props.itemHeight)

const totalScrollableHeight = computed(() => Math.max(0, contentHeight.value - containerHeight.value))

const scrollPercentage = computed(() => {
  if (totalScrollableHeight.value <= 0) return 0
  return Math.min(1, Math.max(0, scrollTop.value / totalScrollableHeight.value))
})

const thumbHeight = computed(() => {
  const ratio = Math.min(1, containerHeight.value / contentHeight.value)
  return Math.max(24, ratio * containerHeight.value)
})

const thumbTop = computed(() => {
  if (totalScrollableHeight.value <= 0) return 0
  return scrollPercentage.value * (containerHeight.value - thumbHeight.value)
})

const visibleRange = computed(() => {
  const start = Math.max(0, Math.floor(scrollTop.value / props.itemHeight) - props.overscan)
  const end = Math.min(
    itemsList.value.length,
    Math.ceil((scrollTop.value + containerHeight.value) / props.itemHeight) + props.overscan
  )
  return { start: Math.max(0, start), end }
})

const visibleItems = computed(() => {
  const { start, end } = visibleRange.value
  return itemsList.value.slice(start, end).map((item, index) => ({
    ...item,
    _virtualIndex: start + index
  }))
})

const containerStyles = computed(() => ({
  height: typeof props.height === 'number' ? `${props.height}px` : props.height,
  minHeight: typeof props.minHeight === 'number' ? `${props.minHeight}px` : props.minHeight,
  maxHeight: typeof props.maxHeight === 'number' ? `${props.maxHeight}px` : props.maxHeight,
  overflowX: 'hidden',
  overflowY: 'auto',
  position: 'relative'
}))

const contentStyles = computed(() => ({
  height: `${contentHeight.value}px`,
  width: '100%',
  transform: `translateY(${scrollTop.value}px)`,
  willChange: 'transform'
}))

const thumbStyles = computed(() => ({
  height: `${thumbHeight.value}px`,
  transform: `translateY(${thumbTop.value}px)`
}))

const showScrollbar = computed(() => contentHeight.value > containerHeight.value)

const getItemKey = (item, index) => {
  if (item && typeof item === 'object') {
    return item[props.keyField] ?? `item-${visibleRange.value.start + index}`
  }
  return `item-${visibleRange.value.start + index}`
}

const getItemText = (item) => {
  if (item && typeof item === 'object') {
    return item[props.itemTextField] ?? String(item)
  }
  return String(item)
}

const getItemStyle = (index) => ({
  position: 'absolute',
  top: 0,
  left: 0,
  width: '100%',
  height: `${props.itemHeight}px`,
  transform: `translateY(${(visibleRange.value.start + index) * props.itemHeight}px)`
})

const saveScrollPosition = () => {
  if (!props.persistScrollKey || !mounted.value) return
  try {
    localStorage.setItem(`scroll_${props.persistScrollKey}`, String(Math.round(scrollTop.value)))
  } catch (e) {
  }
}

const restoreScrollPosition = () => {
  if (!props.persistScrollKey) return
  try {
    const saved = localStorage.getItem(`scroll_${props.persistScrollKey}`)
    if (saved !== null) {
      const targetTop = parseInt(saved, 10)
      if (!isNaN(targetTop)) {
        scrollTop.value = targetTop
        if (containerRef.value) {
          setTimeout(() => {
            if (containerRef.value) {
              containerRef.value.scrollTop = targetTop
            }
          }, 0)
        }
      }
    }
  } catch (e) {
  }
}

const onScroll = (event) => {
  const target = event.target || event.srcElement
  const newScrollTop = Math.max(0, target.scrollTop)
  if (newScrollTop === scrollTop.value) return
  scrollTop.value = newScrollTop
  saveScrollPosition()
  emit('scroll', { scrollTop: newScrollTop, percentage: scrollPercentage.value })

  if (newScrollTop <= 0) {
    emit('scroll-start')
  } else if (newScrollTop >= totalScrollableHeight.value - 1) {
    emit('scroll-end')
  }
}

const onWheel = (event) => {
  if (props.smoothScroll && containerRef.value) {
    event.preventDefault()
    const delta = event.deltaY || event.deltaY
    if (delta) {
      const currentScrollTop = containerRef.value.scrollTop
      const targetScrollTop = Math.max(0, Math.min(totalScrollableHeight.value, currentScrollTop + delta))
      containerRef.value.scrollTo({
        top: targetScrollTop,
        behavior: 'smooth'
      })
    }
  }
}

const onKeydown = (event) => {
  const { key } = event
  const pageSize = Math.max(1, Math.floor(containerHeight.value / props.itemHeight) - 1)

  let newIndex = selectedIndex.value
  let handled = false

  switch (key) {
    case 'ArrowDown':
      newIndex = Math.min(itemsList.value.length - 1, selectedIndex.value + 1)
      handled = true
      break
    case 'ArrowUp':
      newIndex = Math.max(0, selectedIndex.value - 1)
      handled = true
      break
    case 'PageDown':
      newIndex = Math.min(itemsList.value.length - 1, selectedIndex.value + pageSize)
      handled = true
      break
    case 'PageUp':
      newIndex = Math.max(0, selectedIndex.value - pageSize)
      handled = true
      break
    case 'Home':
      newIndex = 0
      handled = true
      break
    case 'End':
      newIndex = itemsList.value.length - 1
      handled = true
      break
  }

  if (handled) {
    event.preventDefault()
    emit('update:selectedIndex', newIndex)
    scrollToIndex(newIndex, { align: 'nearest' })
  }
}

const onItemClick = (index) => {
  const actualIndex = visibleRange.value.start + index
  emit('item-click', { item: itemsList.value[actualIndex], index: actualIndex })
  emit('update:selectedIndex', actualIndex)
}

const onItemHover = (index) => {
  const actualIndex = visibleRange.value.start + index
  emit('item-hover', { item: itemsList.value[actualIndex], index: actualIndex })
}

const scrollToIndex = (index, options = {}) => {
  if (index < 0 || index >= itemsList.value.length) return
  const { align = 'auto', smooth = props.smoothScroll } = options
  const targetScrollTop = index * props.itemHeight

  let finalScrollTop = targetScrollTop
  if (align === 'center') {
    finalScrollTop = targetScrollTop - (containerHeight.value - props.itemHeight) / 2
  } else if (align === 'end') {
    finalScrollTop = targetScrollTop - containerHeight.value + props.itemHeight
  }

  finalScrollTop = Math.max(0, Math.min(totalScrollableHeight.value, finalScrollTop))

  if (smooth) {
    if (containerRef.value) {
      containerRef.value.scrollTo({
        top: finalScrollTop,
        behavior: 'smooth'
      })
    }
    scrollTop.value = finalScrollTop
  } else {
    if (containerRef.value) {
      containerRef.value.scrollTop = finalScrollTop
    }
    scrollTop.value = finalScrollTop
  }
}

const scrollToPosition = (position, smooth = props.smoothScroll) => {
  const finalPosition = Math.max(0, Math.min(totalScrollableHeight.value, position))
  if (smooth) {
    if (containerRef.value) {
      containerRef.value.scrollTo({
        top: finalPosition,
        behavior: 'smooth'
      })
    }
    scrollTop.value = finalPosition
  } else {
    if (containerRef.value) {
      containerRef.value.scrollTop = finalPosition
    }
    scrollTop.value = finalPosition
  }
}

const startDrag = (event) => {
  event.preventDefault()
  isDragging.value = true
  dragStartY.value = event.clientY
  dragStartScrollTop.value = scrollTop.value
  document.body.style.userSelect = 'none'
  document.body.style.cursor = 'grabbing'
}

const onDrag = (event) => {
  if (!isDragging.value) return
  const deltaY = event.clientY - dragStartY.value
  const containerRect = containerRef.value.getBoundingClientRect()
  const ratio = totalScrollableHeight.value / (containerRect.height - thumbHeight.value)
  const deltaScroll = deltaY * ratio
  const newScrollTop = Math.max(0, Math.min(totalScrollableHeight.value, dragStartScrollTop.value + deltaScroll))
  containerRef.value.scrollTop = newScrollTop
}

const stopDrag = () => {
  isDragging.value = false
  document.body.style.userSelect = ''
  document.body.style.cursor = ''
}

const updateContainerHeight = () => {
  if (containerRef.value) {
    const h = containerRef.value.clientHeight
    if (h && h > 0) {
      containerHeight.value = h
    } else {
      if (typeof props.height === 'number') {
        containerHeight.value = props.height
      } else if (typeof props.height === 'string') {
        const m = props.height.match(/^\\s*(\\d+)\\s*px\\s*$/i)
        if (m) {
          containerHeight.value = parseInt(m[1], 10)
        }
      }
    }
  }
}

const resizeObserver = shallowRef(null)

onMounted(() => {
  mounted.value = true
  updateContainerHeight()

  resizeObserver.value = new ResizeObserver(() => {
    updateContainerHeight()
  })

  if (containerRef.value) {
    resizeObserver.value.observe(containerRef.value)
  }

  restoreScrollPosition()

  if (containerRef.value) {
    containerRef.value.addEventListener('scroll', onScroll, { passive: true })
  }
})

onUnmounted(() => {
  mounted.value = false
  if (resizeObserver.value && containerRef.value) {
    resizeObserver.value.unobserve(containerRef.value)
  }
  if (containerRef.value) {
    containerRef.value.removeEventListener('scroll', onScroll)
  }
})

watch(() => itemsList.value.length, () => {
  nextTick(() => {
    updateContainerHeight()
  })
})

watch(() => props.persistScrollKey, (newKey, oldKey) => {
  if (oldKey && oldKey !== newKey) {
    try {
      localStorage.removeItem(`scroll_${oldKey}`)
    } catch (e) {
    }
  }
  if (newKey) {
    restoreScrollPosition()
  }
})

defineExpose({
  scrollToIndex,
  scrollToPosition,
  scrollToTop: () => scrollToPosition(0, false),
  scrollToBottom: () => scrollToPosition(totalScrollableHeight.value, false),
  getScrollTop: () => scrollTop.value,
  getScrollPercentage: () => scrollPercentage.value,
  refresh: updateContainerHeight
})
</script>

<style scoped>
.virtual-scroll-container {
  scrollbar-width: thin;
  scrollbar-color: transparent transparent;
}

.virtual-scroll-container::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.virtual-scroll-container::-webkit-scrollbar-track {
  background: transparent;
}

.virtual-scroll-container::-webkit-scrollbar-thumb {
  background-color: rgba(203, 213, 225, 0.5);
  border-radius: 3px;
  opacity: 0;
  transition: opacity 0.2s ease, background-color 0.2s ease;
}

.virtual-scroll-container:hover::-webkit-scrollbar-thumb,
.virtual-scroll-container:focus-within::-webkit-scrollbar-thumb,
.virtual-scroll-container.dragging::-webkit-scrollbar-thumb {
  opacity: 1;
}

.virtual-scroll-container::-webkit-scrollbar-thumb:hover {
  background-color: rgba(148, 163, 184, 0.8);
}

.virtual-scroll-container::-webkit-scrollbar-thumb:active {
  background-color: rgba(100, 116, 139, 1);
}

.virtual-scroll-container {
  scrollbar-color: rgba(203, 213, 225, 0.5) transparent;
}

.virtual-scroll-container:hover {
  scrollbar-color: rgba(203, 213, 225, 0.8) transparent;
}

.virtual-scroll-content {
  will-change: transform;
  contain: strict;
}

.virtual-scroll-item {
  contain: strict;
  will-change: transform;
}

.virtual-scroll-scrollbar {
  position: absolute;
  right: 0;
  top: 0;
  width: 8px;
  height: 100%;
  background: transparent;
  z-index: 10;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.virtual-scroll-container:hover .virtual-scroll-scrollbar,
.virtual-scroll-scrollbar:hover,
.virtual-scroll-container.dragging .virtual-scroll-scrollbar {
  opacity: 1;
}

.scrollbar-thumb {
  position: absolute;
  left: 0;
  width: 100%;
  min-width: 6px;
  background: rgba(148, 163, 184, 0.6);
  border-radius: 3px;
  cursor: grab;
  transition: background-color 0.15s ease, transform 0.15s ease;
}

.scrollbar-thumb:hover {
  background: rgba(100, 116, 139, 0.9);
  transform: scaleX(1.1);
}

.scrollbar-thumb:active {
  cursor: grabbing;
  background: rgba(71, 85, 105, 1);
}

.drag-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 9999;
  cursor: grabbing;
}

.default-item-content {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  padding: 0 12px;
  box-sizing: border-box;
}

.virtual-scroll-item {
  display: flex;
  align-items: center;
  box-sizing: border-box;
}

.virtual-scroll-item:focus {
  outline: none;
}

.virtual-scroll-item:focus-visible {
  outline: 2px solid #0052D9;
  outline-offset: -2px;
}

.virtual-scroll-item[aria-selected="true"] {
  background-color: rgba(0, 82, 217, 0.1);
}

.virtual-scroll-item:hover {
  background-color: rgba(0, 0, 0, 0.02);
}

.virtual-scroll-item[aria-selected="true"]:hover {
  background-color: rgba(0, 82, 217, 0.15);
}

@media (prefers-reduced-motion: reduce) {
  .virtual-scroll-content,
  .virtual-scroll-item,
  .scrollbar-thumb {
    transition: none;
  }
}

@media (max-width: 768px) {
  .virtual-scroll-scrollbar {
    width: 4px;
  }

  .scrollbar-thumb {
    border-radius: 2px;
    min-width: 4px;
  }
}
</style>
