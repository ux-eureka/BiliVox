import { mount } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import VirtualScrollList from '../../src/components/VirtualScrollList.vue'

const createTestItems = (count) => {
  return Array.from({ length: count }, (_, i) => ({
    id: `item-${i}`,
    title: `测试项目 ${i + 1}`,
    description: `这是第 ${i + 1} 个测试项目的描述`
  }))
}

describe('VirtualScrollList', () => {
  let wrapper

  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
    if (wrapper) {
      wrapper.unmount()
    }
    try {
      localStorage.clear()
    } catch (e) {
    }
  })

  describe('基础渲染', () => {
    it('应该渲染空的列表容器', () => {
      wrapper = mount(VirtualScrollList, {
        props: {
          items: []
        }
      })

      const container = wrapper.find('.virtual-scroll-container')
      expect(container.exists()).toBe(true)

      const content = wrapper.find('.virtual-scroll-content')
      expect(content.exists()).toBe(true)

      expect(content.attributes('style')).toContain('height: 0px')
    })

    it('应该正确渲染列表项', async () => {
      const items = createTestItems(10)

      wrapper = mount(VirtualScrollList, {
        props: {
          items,
          itemHeight: 50
        }
      })

      await nextTick()

      const renderedItems = wrapper.findAll('.virtual-scroll-item')
      expect(renderedItems.length).toBeGreaterThan(0)

      expect(wrapper.find('.virtual-scroll-content').attributes('style')).toContain('height: 500px')
    })

    it('应该使用自定义高度', () => {
      wrapper = mount(VirtualScrollList, {
        props: {
          items: createTestItems(5),
          height: '300px',
          maxHeight: '400px',
          itemHeight: 40
        }
      })

      const container = wrapper.find('.virtual-scroll-container')
      expect(container.attributes('style')).toContain('height: 300px')
      expect(container.attributes('style')).toContain('max-height: 400px')
    })
  })

  describe('滚动功能', () => {
    it('应该正确计算可见范围', async () => {
      const items = createTestItems(100)
      wrapper = mount(VirtualScrollList, {
        props: {
          items,
          itemHeight: 50,
          overscan: 2
        }
      })

      await nextTick()

      const visibleRange = wrapper.vm.visibleRange
      expect(visibleRange.start).toBe(0)
      expect(visibleRange.end).toBeLessThanOrEqual(items.length + 4)
    })

    it('应该处理滚动事件', async () => {
      const items = createTestItems(50)
      wrapper = mount(VirtualScrollList, {
        props: {
          items,
          itemHeight: 50
        }
      })

      await nextTick()

      wrapper.vm.onScroll({ target: { scrollTop: 200 } })

      expect(wrapper.emitted('scroll')).toBeTruthy()
      expect(wrapper.emitted('scroll')[0][0]).toEqual({
        scrollTop: 200,
        percentage: expect.any(Number)
      })
    })

    it('应该支持平滑滚动', async () => {
      const items = createTestItems(20)
      wrapper = mount(VirtualScrollList, {
        props: {
          items,
          itemHeight: 40,
          smoothScroll: true
        }
      })

      await nextTick()

      wrapper.vm.scrollToIndex(5)
      await nextTick()

      expect(wrapper.vm.getScrollTop()).toBeGreaterThanOrEqual(0)
    })
  })

  describe('键盘导航', () => {
    it('应该支持方向键导航', async () => {
      const items = createTestItems(10)
      wrapper = mount(VirtualScrollList, {
        props: {
          items,
          itemHeight: 50,
          selectedIndex: 2
        }
      })

      await nextTick()

      const container = wrapper.find('.virtual-scroll-container')

      await container.trigger('keydown', { key: 'ArrowDown' })
      await nextTick()

      expect(wrapper.emitted('update:selectedIndex')).toBeTruthy()
      expect(wrapper.emitted('update:selectedIndex')[0][0]).toBe(3)
    })

    it('应该支持PageUp/PageDown', async () => {
      const items = createTestItems(30)
      wrapper = mount(VirtualScrollList, {
        props: {
          items,
          itemHeight: 50,
          selectedIndex: 10
        }
      })

      await nextTick()

      const container = wrapper.find('.virtual-scroll-container')

      await container.trigger('keydown', { key: 'PageDown' })
      await nextTick()

      const emitted = wrapper.emitted('update:selectedIndex')
      expect(emitted).toBeTruthy()
      expect(emitted[0][0]).toBeGreaterThan(10)
    })

    it('应该支持Home/End键', async () => {
      const items = createTestItems(20)
      wrapper = mount(VirtualScrollList, {
        props: {
          items,
          itemHeight: 50,
          selectedIndex: 10
        }
      })

      await nextTick()

      const container = wrapper.find('.virtual-scroll-container')

      await container.trigger('keydown', { key: 'Home' })
      await nextTick()

      expect(wrapper.emitted('update:selectedIndex')[0][0]).toBe(0)
    })
  })

  describe('项目交互', () => {
    it('应该触发项目点击事件', async () => {
      const items = createTestItems(5)
      wrapper = mount(VirtualScrollList, {
        props: {
          items,
          itemHeight: 60
        }
      })

      await nextTick()

      const firstItem = wrapper.find('.virtual-scroll-item')
      await firstItem.trigger('click')

      expect(wrapper.emitted('item-click')).toBeTruthy()
      expect(wrapper.emitted('item-click')[0][0]).toEqual({
        item: items[0],
        index: 0
      })
    })

    it('应该支持悬停事件', async () => {
      const items = createTestItems(5)
      wrapper = mount(VirtualScrollList, {
        props: {
          items,
          itemHeight: 60
        }
      })

      await nextTick()

      const firstItem = wrapper.find('.virtual-scroll-item')
      await firstItem.trigger('mouseenter')

      expect(wrapper.emitted('item-hover')).toBeTruthy()
    })

    it('应该正确显示选中状态', async () => {
      const items = createTestItems(5)
      wrapper = mount(VirtualScrollList, {
        props: {
          items,
          itemHeight: 60,
          selectedIndex: 2
        }
      })

      await nextTick()

      const itemsWrapper = wrapper.findAll('.virtual-scroll-item')
      expect(itemsWrapper[2].attributes('aria-selected')).toBe('true')
    })
  })

  describe('滚动条功能', () => {
    it('应该在内容超出时显示滚动条', async () => {
      const items = createTestItems(50)
      wrapper = mount(VirtualScrollList, {
        props: {
          items,
          itemHeight: 50,
          height: '200px'
        }
      })

      await nextTick()

      const scrollbar = wrapper.find('.virtual-scroll-scrollbar')
      expect(scrollbar.exists()).toBe(true)
    })

    it('应该隐藏滚动条当内容未超出', () => {
      const items = createTestItems(3)
      wrapper = mount(VirtualScrollList, {
        props: {
          items,
          itemHeight: 100,
          height: '500px'
        }
      })

      const scrollbar = wrapper.find('.virtual-scroll-scrollbar')
      expect(scrollbar.exists()).toBe(false)
    })

    it('应该正确计算滚动条thumb位置', async () => {
      const items = createTestItems(100)
      wrapper = mount(VirtualScrollList, {
        props: {
          items,
          itemHeight: 50,
          height: '300px'
        }
      })

      await nextTick()

      const thumbStyles = wrapper.find('.scrollbar-thumb').attributes('style')
      expect(thumbStyles).toContain('transform')
    })
  })

  describe('滚动位置记忆', () => {
    it('应该保存滚动位置到localStorage', async () => {
      const items = createTestItems(50)
      wrapper = mount(VirtualScrollList, {
        props: {
          items,
          itemHeight: 50,
          height: '300px',
          persistScrollKey: 'test-scroll-key'
        }
      })

      await nextTick()

      wrapper.vm.onScroll({ target: { scrollTop: 500 } })

      vi.advanceTimersByTime(200)

      const saved = localStorage.getItem('scroll_test-scroll-key')
      expect(saved).toBe('500')
    })

    it('应该从localStorage恢复滚动位置', async () => {
      localStorage.setItem('scroll_restore-key', '300')

      const items = createTestItems(50)
      wrapper = mount(VirtualScrollList, {
        props: {
          items,
          itemHeight: 50,
          height: '300px',
          persistScrollKey: 'restore-key'
        }
      })

      await nextTick()
      vi.advanceTimersByTime(100)

      expect(wrapper.vm.getScrollTop()).toBe(300)
    })
  })

  describe('动态内容', () => {
    it('应该在项目添加后更新滚动区域', async () => {
      const items = ref(createTestItems(10))
      wrapper = mount(VirtualScrollList, {
        props: {
          items: items,
          itemHeight: 50
        }
      })

      await nextTick()

      const initialHeight = wrapper.find('.virtual-scroll-content').attributes('style')

      items.value = [...items.value, ...createTestItems(10)]
      await nextTick()
      await nextTick()
      wrapper.vm.$forceUpdate()
      await nextTick()

      const newHeight = wrapper.find('.virtual-scroll-content').attributes('style')
      expect(newHeight).not.toBe(initialHeight)
    })

    it('应该在项目清空后更新视图', async () => {
      const items = ref(createTestItems(20))
      wrapper = mount(VirtualScrollList, {
        props: {
          items: items,
          itemHeight: 50
        }
      })

      await nextTick()

      items.value = []
      await nextTick()
      await nextTick()
      wrapper.vm.$forceUpdate()
      await nextTick()

      const content = wrapper.find('.virtual-scroll-content')
      expect(content.attributes('style')).toContain('height: 0px')
    })
  })

  describe('暴露方法', () => {
    it('应该暴露scrollToIndex方法', async () => {
      const items = createTestItems(50)
      wrapper = mount(VirtualScrollList, {
        props: {
          items,
          itemHeight: 50
        }
      })

      await nextTick()

      expect(typeof wrapper.vm.scrollToIndex).toBe('function')
      wrapper.vm.scrollToIndex(10)
      await nextTick()

      expect(wrapper.vm.getScrollTop()).toBe(500)
    })

    it('应该暴露scrollToTop和scrollToBottom方法', async () => {
      const items = createTestItems(50)
      wrapper = mount(VirtualScrollList, {
        props: {
          items,
          itemHeight: 50,
          height: '300px'
        }
      })

      await nextTick()

      wrapper.vm.scrollToIndex(30)
      await nextTick()

      expect(typeof wrapper.vm.scrollToTop).toBe('function')
      expect(typeof wrapper.vm.scrollToBottom).toBe('function')

      wrapper.vm.scrollToBottom()
      await nextTick()
    })
  })

  describe('性能优化', () => {
    it('应该使用虚拟滚动只渲染可见项目', async () => {
      const items = createTestItems(1000)
      wrapper = mount(VirtualScrollList, {
        props: {
          items,
          itemHeight: 50,
          height: '400px',
          overscan: 5
        }
      })

      await nextTick()

      const renderedItems = wrapper.findAll('.virtual-scroll-item')

      expect(renderedItems.length).toBeLessThan(50)
      expect(wrapper.find('.virtual-scroll-content').attributes('style')).toContain('height: 50000px')
    })

    it('应该正确使用will-change优化', async () => {
      const items = createTestItems(100)
      wrapper = mount(VirtualScrollList, {
        props: {
          items,
          itemHeight: 50
        }
      })

      await nextTick()

      const content = wrapper.find('.virtual-scroll-content')
      expect(content.attributes('style')).toContain('will-change')
    })
  })

  describe('无障碍', () => {
    it('应该设置正确的role属性', () => {
      const items = createTestItems(5)
      wrapper = mount(VirtualScrollList, {
        props: {
          items,
          itemHeight: 50,
          ariaLabel: '测试列表'
        }
      })

      const container = wrapper.find('.virtual-scroll-container')
      expect(container.attributes('role')).toBe('listbox')
      expect(container.attributes('aria-label')).toBe('测试列表')
    })

    it('应该为每个项目设置正确的role属性', async () => {
      const items = createTestItems(5)
      wrapper = mount(VirtualScrollList, {
        props: {
          items,
          itemHeight: 50
        }
      })

      await nextTick()

      const itemsWrapper = wrapper.findAll('.virtual-scroll-item')
      itemsWrapper.forEach(item => {
        expect(item.attributes('role')).toBe('option')
      })
    })

    it('应该支持键盘聚焦', async () => {
      const items = createTestItems(5)
      wrapper = mount(VirtualScrollList, {
        props: {
          items,
          itemHeight: 50
        }
      })

      await nextTick()

      const container = wrapper.find('.virtual-scroll-container')
      expect(container.attributes('tabindex')).toBe('0')
    })
  })

  describe('RTL支持', () => {
    it('应该支持RTL模式', async () => {
      const items = createTestItems(5)
      wrapper = mount(VirtualScrollList, {
        props: {
          items,
          itemHeight: 50,
          RTL: true
        }
      })

      await nextTick()

      expect(wrapper.vm.RTL).toBe(true)
    })
  })

  describe('自定义槽位', () => {
    it('应该渲染默认项目模板', async () => {
      const items = createTestItems(3)
      wrapper = mount(VirtualScrollList, {
        props: {
          items,
          itemHeight: 60
        }
      })

      await nextTick()

      expect(wrapper.find('.default-item-content').exists()).toBe(true)
    })
  })
})

import { ref, nextTick, h } from 'vue'
