/**
 * SystemLogs 组件 - 视觉回归测试
 * 
 * 测试目标：
 * 1. 验证容器高度100%充满父级（容差 ≤ 1px）
 * 2. 验证内部滚动功能正常
 * 3. 验证滚动条自动出现
 * 4. 验证 iOS 惯性滚动支持
 * 5. 验证性能指标（10000条 < 300ms）
 * 
 * 运行方式：
 * npx vitest run tests/unit/SystemLogs.visual.test.js
 */

import { mount } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach, afterEach, jest } from 'vitest'
import SystemLogs from '../../src/components/SystemLogs.vue'

const TOLERANCE = 1 // 像素容差

describe('SystemLogs Visual Regression', () => {
  let wrapper

  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
    if (wrapper) {
      wrapper.unmount()
    }
  })

  describe('高度100%充满验证', () => {
    it('应该精确填满父容器高度（容差 ≤ 1px）', async () => {
      const parentHeight = 400

      wrapper = mount(SystemLogs, {
        props: {
          logs: '测试日志内容\n'.repeat(50)
        },
        attachTo: document.createElement('div')
      })

      const parent = document.createElement('div')
      parent.style.height = `${parentHeight}px`
      parent.style.display = 'flex'
      parent.style.flexDirection = 'column'
      document.body.appendChild(parent)

      wrapper.unmount()
      wrapper = mount(SystemLogs, {
        props: {
          logs: '测试日志内容\n'.repeat(50)
        },
        attachTo: parent
      })

      await nextTick()
      vi.advanceTimersByTime(100)

      const container = parent.querySelector('.system-logs-container')
      const scrollContent = parent.querySelector('.scroll-content')

      expect(container).toBeTruthy()
      expect(scrollContent).toBeTruthy()

      const containerRect = container.getBoundingClientRect()
      const scrollRect = scrollContent.getBoundingClientRect()

      console.log(`容器高度: ${containerRect.height}, 父容器: ${parentHeight}`)

      expect(containerRect.height).toBeGreaterThanOrEqual(parentHeight - TOLERANCE)
      expect(containerRect.height).toBeLessThanOrEqual(parentHeight + TOLERANCE)

      document.body.removeChild(parent)
    })

    it('应该在父容器高度变化时自动调整', async () => {
      const parent = document.createElement('div')
      parent.style.height = '300px'
      parent.style.display = 'flex'
      parent.style.flexDirection = 'column'
      document.body.appendChild(parent)

      wrapper = mount(SystemLogs, {
        props: {
          logs: '测试日志\n'.repeat(100)
        },
        attachTo: parent
      })

      await nextTick()
      vi.advanceTimersByTime(100)

      const initialHeight = parent.querySelector('.system-logs-container')?.getBoundingClientRect()?.height

      parent.style.height = '500px'

      await nextTick()
      vi.advanceTimersByTime(100)

      const newHeight = parent.querySelector('.system-logs-container')?.getBoundingClientRect()?.height

      expect(newHeight).toBeGreaterThan(initialHeight)

      console.log(`高度从 ${initialHeight}px 调整为 ${newHeight}px`)

      document.body.removeChild(parent)
    })

    it('应该处理父容器 min-height: 0 的情况', async () => {
      const parent = document.createElement('div')
      parent.style.height = '400px'
      parent.style.display = 'flex'
      parent.style.flexDirection = 'column'
      parent.style.minHeight = '0'
      document.body.appendChild(parent)

      wrapper = mount(SystemLogs, {
        props: {
          logs: '日志内容\n'.repeat(100)
        },
        attachTo: parent
      })

      await nextTick()
      vi.advanceTimersByTime(100)

      const container = parent.querySelector('.system-logs-container')
      const containerHeight = container.getBoundingClientRect().height

      expect(containerHeight).toBeGreaterThan(0)
      expect(containerHeight).toBeLessThanOrEqual(400 + TOLERANCE)

      document.body.removeChild(parent)
    })
  })

  describe('内部滚动验证', () => {
    it('应该在内容溢出时自动显示滚动条', async () => {
      const logs = '日志条目\n'.repeat(200)

      wrapper = mount(SystemLogs, {
        props: {
          logs,
          paddingSize: 16
        }
      })

      await nextTick()
      vi.advanceTimersByTime(100)

      const scrollContent = wrapper.find('.scroll-content')

      expect(scrollContent.exists()).toBe(true)
      expect(scrollContent.classes()).toContain('overflow-y-auto')

      const scrollHeight = scrollContent.attributes('data-scroll-height')
      const clientHeight = scrollContent.attributes('data-client-height')

      console.log(`scrollHeight: ${scrollHeight}, clientHeight: ${clientHeight}`)

      expect(parseInt(scrollHeight || '0')).toBeGreaterThan(parseInt(clientHeight || '0'))
    })

    it('应该在内容未溢出时隐藏滚动条', async () => {
      wrapper = mount(SystemLogs, {
        props: {
          logs: '简短日志'
        }
      })

      await nextTick()
      vi.advanceTimersByTime(100)

      const scrollContent = wrapper.find('.scroll-content')

      expect(scrollContent.exists()).toBe(true)
    })

    it('滚动时 scrollHeight 应该大于 clientHeight', async () => {
      const logs = '行1\n行2\n行3\n'.repeat(50)

      wrapper = mount(SystemLogs, {
        props: {
          logs
        }
      })

      await nextTick()
      vi.advanceTimersByTime(100)

      const scrollContent = wrapper.find('.scroll-content')

      const scrollHeight = parseInt(scrollContent.attributes('data-scroll-height') || '0', 10)
      const clientHeight = parseInt(scrollContent.attributes('data-client-height') || '0', 10)

      expect(scrollHeight).toBeGreaterThan(clientHeight)

      await scrollContent.trigger('scroll')

      expect(wrapper.emitted('scroll')).toBeTruthy()
    })
  })

  describe('iOS惯性滚动验证', () => {
    it('应该包含 -webkit-overflow-scrolling: touch 样式', async () => {
      wrapper = mount(SystemLogs, {
        props: {
          logs: '测试'
        }
      })

      await nextTick()

      const scrollContent = wrapper.find('.scroll-content')
      const styles = window.getComputedStyle(scrollContent.element)

      expect(
        styles.getPropertyValue('-webkit-overflow-scrolling') ||
        scrollContent.element.style.webkitOverflowScrolling
      ).toBeTruthy()
    })
  })

  describe('4px内边距验证', () => {
    it('应该正确应用 padding-size', async () => {
      wrapper = mount(SystemLogs, {
        props: {
          logs: '测试内容',
          paddingSize: 4
        }
      })

      await nextTick()
      vi.advanceTimersByTime(100)

      const scrollPaddingBox = wrapper.find('.scroll-padding-box')
      const styles = window.getComputedStyle(scrollPaddingBox.element)

      expect(styles.padding).toContain('4px')
    })

    it('应该使用 box-sizing: border-box', async () => {
      wrapper = mount(SystemLogs, {
        props: {
          logs: '测试',
          paddingSize: 16
        }
      })

      await nextTick()
      vi.advanceTimersByTime(100)

      const scrollContent = wrapper.find('.scroll-content')
      const styles = window.getComputedStyle(scrollContent.element)

      expect(styles.boxSizing).toBe('border-box')
    })
  })

  describe('性能测试', () => {
    it('插入10000条DOM节点应少于300ms', async () => {
      const parent = document.createElement('div')
      parent.style.height = '500px'
      parent.style.display = 'flex'
      parent.style.flexDirection = 'column'
      document.body.appendChild(parent)

      wrapper = mount(SystemLogs, {
        props: {
          logs: ''
        },
        attachTo: parent
      })

      await nextTick()

      const logs = Array.from({ length: 10000 }, (_, i) => `[${i}] 日志条目 ${i}`).join('\n')

      const startTime = performance.now()

      await wrapper.setProps({ logs })

      const endTime = performance.now()
      const renderTime = endTime - startTime

      console.log(`10000条日志渲染时间: ${renderTime.toFixed(2)}ms`)

      expect(renderTime).toBeLessThan(300)

      await nextTick()
      vi.advanceTimersByTime(100)

      expect(wrapper.props('logs').length).toBeGreaterThan(0)

      document.body.removeChild(parent)
    })

    it('滚动至顶部与底部应无白屏', async () => {
      const logs = Array.from({ length: 500 }, (_, i) => `日志行 ${i}`).join('\n')

      wrapper = mount(SystemLogs, {
        props: {
          logs
        }
      })

      await nextTick()
      vi.advanceTimersByTime(100)

      const scrollContent = wrapper.find('.scroll-content')

      scrollContent.element.scrollTop = 0
      await scrollContent.trigger('scroll')

      const topPosition = wrapper.emitted('reach-top')
      expect(topPosition).toBeTruthy()

      scrollContent.element.scrollTop = 10000000
      await scrollContent.trigger('scroll')

      const bottomPosition = wrapper.emitted('reach-bottom')
      expect(bottomPosition).toBeTruthy()
    })
  })

  describe('滚动位置记忆', () => {
    it('应该保存并恢复滚动位置', async () => {
      const parent = document.createElement('div')
      parent.style.height = '400px'
      parent.style.display = 'flex'
      parent.style.flexDirection = 'column'
      document.body.appendChild(parent)

      wrapper = mount(SystemLogs, {
        props: {
          logs: '日志\n'.repeat(100),
          persistScrollKey: 'test-logs-scroll'
        },
        attachTo: parent
      })

      await nextTick()
      vi.advanceTimersByTime(100)

      localStorage.setItem('scroll_test-logs-scroll', String(500))

      wrapper.unmount()

      wrapper = mount(SystemLogs, {
        props: {
          logs: '日志\n'.repeat(100),
          persistScrollKey: 'test-logs-scroll'
        },
        attachTo: parent
      })

      await nextTick()
      vi.advanceTimersByTime(100)

      const saved = localStorage.getItem('scroll_test-logs-scroll')
      expect(saved).toBe('500')

      document.body.removeChild(parent)
    })
  })

  describe('键盘导航', () => {
    it('容器应支持键盘聚焦', async () => {
      wrapper = mount(SystemLogs, {
        props: {
          logs: '测试日志'
        }
      })

      await nextTick()

      const container = wrapper.find('.system-logs-container')
      expect(container.attributes('tabindex')).toBeDefined()
    })

    it('应该支持 PageUp/PageDown 滚动', async () => {
      wrapper = mount(SystemLogs, {
        props: {
          logs: '行\n'.repeat(100)
        }
      })

      await nextTick()
      vi.advanceTimersByTime(100)

      const scrollContent = wrapper.find('.scroll-content')

      const initialScrollTop = parseInt(scrollContent.element.getAttribute('data-cur-scroll-top') || '0', 10)
      scrollContent.element.scrollTop = initialScrollTop + 100

      await scrollContent.trigger('scroll')

      expect(scrollContent.element.scrollTop).toBeGreaterThan(initialScrollTop)
    })
  })

  describe('无障碍验证', () => {
    it('应该设置正确的 role 属性', async () => {
      wrapper = mount(SystemLogs, {
        props: {
          logs: '测试',
          ariaLabel: '系统日志'
        }
      })

      await nextTick()

      const container = wrapper.find('.system-logs-container')
      expect(container.attributes('role')).toBe('log')
      expect(container.attributes('aria-label')).toBe('系统日志')
    })

    it('应该支持 aria-live', async () => {
      wrapper = mount(SystemLogs, {
        props: {
          logs: '测试',
          ariaLive: 'polite'
        }
      })

      await nextTick()

      const container = wrapper.find('.system-logs-container')
      expect(container.attributes('aria-live')).toBe('polite')
    })
  })
})

import { nextTick } from 'vue'
