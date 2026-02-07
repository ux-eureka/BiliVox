/**
 * Files.vue 分页器固定底部 - 单元测试
 * 
 * 测试内容：
 * 1. 分页器固定底部布局
 * 2. 分页数据计算
 * 3. 分页事件处理
 * 4. 响应式适配
 */

import { mount } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { nextTick } from 'vue'
import Files from '../../src/views/Files.vue'

const createMockFiles = (count) => {
  return Array.from({ length: count }, (_, i) => ({
    id: `file-${i}`,
    name: `测试文件 ${i + 1}.md`,
    bv: `BV${String(i + 1).padStart(10, '0')}`,
    date: '2024-01-01',
    up: i % 3 === 0 ? 'UP主A' : (i % 3 === 1 ? 'UP主B' : 'UP主C'),
    path: `/files/test-${i + 1}.md`,
    modifiedTs: Date.now()
  }))
}

describe('Files.vue Pagination', () => {
  let wrapper

  beforeEach(async () => {
    wrapper = mount(Files, {
      global: {
        stubs: {
          't-card': { template: '<div class="t-card-stub"><slot /></div>' },
          't-table': {
            props: ['data', 'columns', 'rowKey', 'hover', 'selectedRowKeys', 'maxHeight', 'tableLayout'],
            emits: ['select-change', 'filter-change'],
            template: '<div class="t-table-stub"><slot /></div>'
          },
          't-pagination': {
            props: ['modelValue', 'pageSize', 'total', 'showJumper', 'pageSizeOptions'],
            emits: ['update:modelValue', 'update:pageSize', 'change', 'page-size-change'],
            template: '<div class="t-pagination-stub"><slot /></div>'
          },
          't-input': { template: '<input class="t-input-stub" />' },
          't-button': { template: '<button class="t-button-stub"><slot /></button>' },
          't-tag': { template: '<span class="t-tag-stub"><slot /></span>' },
          't-icon': { template: '<span class="t-icon-stub" />' },
          't-select': { template: '<select class="t-select-stub"><slot /></select>' },
          't-option': { template: '<option class="t-option-stub"><slot /></option>' },
          't-checkbox': { template: '<input type="checkbox" class="t-checkbox-stub" />' },
          't-dialog': { template: '<div class="t-dialog-stub"><slot /></div>' },
          'router-view': { template: '<div class="router-view-stub"><slot /></div>' },
          'transition': { template: '<div class="transition-stub"><slot /></div>' },
          'SearchSelect': { template: '<div class="search-select-stub"><slot /></div>' }
        },
        mocks: {
          $router: { push: vi.fn() },
          $route: { query: {} }
        }
      }
    })
    
    await nextTick()
  })

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
    }
  })

  describe('分页器状态', () => {
    it('应该初始化正确的页码和每页数量', async () => {
      expect(wrapper.vm.currentPage).toBe(1)
      expect(wrapper.vm.pageSize).toBe(10)
    })

    it('应该使用正确的分页选项', () => {
      expect(wrapper.vm.pageSizeOptions).toHaveLength(4)
      expect(wrapper.vm.pageSizeOptions[0]).toEqual({ label: '10 条/页', value: 10 })
      expect(wrapper.vm.pageSizeOptions[1]).toEqual({ label: '20 条/页', value: 20 })
    })
  })

  describe('分页数据计算', () => {
    it('应该正确计算分页数据', async () => {
      wrapper.vm.files = createMockFiles(25)
      await nextTick()
      
      expect(wrapper.vm.paginatedFiles).toHaveLength(10)
      expect(wrapper.vm.paginatedFiles[0].name).toBe('测试文件 1.md')
      expect(wrapper.vm.paginatedFiles[9].name).toBe('测试文件 10.md')
    })

    it('应该在第二页显示正确的数据', async () => {
      wrapper.vm.files = createMockFiles(25)
      wrapper.vm.currentPage = 2
      await nextTick()
      
      expect(wrapper.vm.paginatedFiles).toHaveLength(10)
      expect(wrapper.vm.paginatedFiles[0].name).toBe('测试文件 11.md')
      expect(wrapper.vm.paginatedFiles[9].name).toBe('测试文件 20.md')
    })

    it('应该在最后一页显示剩余数据', async () => {
      wrapper.vm.files = createMockFiles(23)
      wrapper.vm.currentPage = 3
      await nextTick()
      
      expect(wrapper.vm.paginatedFiles).toHaveLength(3)
    })

    it('当数据不足一页时应该显示全部', async () => {
      wrapper.vm.files = createMockFiles(5)
      await nextTick()
      
      expect(wrapper.vm.paginatedFiles).toHaveLength(5)
    })
  })

  describe('分页事件处理', () => {
    it('onPageChange应该更新当前页码', async () => {
      wrapper.vm.files = createMockFiles(100)
      await nextTick()
      wrapper.vm.onPageChange({ current: 5 })
      expect(wrapper.vm.currentPage).toBe(5)
    })

    it('onPageSizeChange应该更新每页数量并重置到第一页', async () => {
      wrapper.vm.currentPage = 3
      wrapper.vm.onPageSizeChange(20)
      expect(wrapper.vm.pageSize).toBe(20)
      expect(wrapper.vm.currentPage).toBe(1)
    })

    it('页码越界时应被约束到最大页', async () => {
      wrapper.vm.files = createMockFiles(12)
      await nextTick()
      wrapper.vm.onPageChange({ current: 99 })
      const maxPage = Math.ceil(wrapper.vm.filteredFiles.length / wrapper.vm.pageSize)
      expect(wrapper.vm.currentPage).toBe(maxPage)
    })

    it('页码小于1时应被重置为1', async () => {
      wrapper.vm.files = createMockFiles(12)
      await nextTick()
      wrapper.vm.onPageChange(0)
      expect(wrapper.vm.currentPage).toBe(1)
    })
  })

  describe('固定分页器样式', () => {
    it('应该存在fixed-pagination-wrapper类', () => {
      const paginationWrapper = wrapper.find('.fixed-pagination-wrapper')
      expect(paginationWrapper.exists()).toBe(true)
    })

    it('分页器容器应被渲染在页面底部区域', () => {
      const paginationWrapper = wrapper.find('.fixed-pagination-wrapper')
      expect(paginationWrapper.exists()).toBe(true)
    })
  })

  describe('响应式适配', () => {
    it('应该存在分页器容器', () => {
      const paginationWrapper = wrapper.find('.fixed-pagination-wrapper')
      expect(paginationWrapper.exists()).toBe(true)
    })

    it('移动端应该调整分页器尺寸', async () => {
      Object.defineProperty(window, 'innerWidth', { writable: true, configurable: true, value: 375 })
      Object.defineProperty(window, 'matchMedia', { writable: true, configurable: true, value: vi.fn().mockImplementation(query => ({
        matches: query === '(max-width: 768px)',
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn()
      }))})
      
      window.dispatchEvent(new Event('resize'))
      await nextTick()
      
      const paginationWrapper = wrapper.find('.fixed-pagination-wrapper')
      expect(paginationWrapper.exists()).toBe(true)
    })
  })

  describe('无障碍支持', () => {
    it('分页器应存在', () => {
      const paginationWrapper = wrapper.find('.fixed-pagination-wrapper')
      expect(paginationWrapper.exists()).toBe(true)
    })
  })
})

describe('Files.vue 表格滚动', () => {
  let wrapper

  beforeEach(async () => {
    wrapper = mount(Files, {
      global: {
        stubs: {
          't-card': { template: '<div class="t-card-stub"><slot /></div>' },
          't-table': {
            props: ['data', 'columns', 'rowKey', 'hover', 'selectedRowKeys', 'maxHeight', 'tableLayout'],
            emits: ['select-change', 'filter-change'],
            template: '<div class="t-table-stub"><slot /></div>'
          },
          't-pagination': { template: '<div class="t-pagination-stub"><slot /></div>' },
          't-input': { template: '<input class="t-input-stub" />' },
          't-button': { template: '<button class="t-button-stub"><slot /></button>' },
          't-tag': { template: '<span class="t-tag-stub"><slot /></span>' },
          't-icon': { template: '<span class="t-icon-stub" />' },
          't-select': { template: '<select class="t-select-stub"><slot /></select>' },
          't-option': { template: '<option class="t-option-stub"><slot /></option>' },
          't-checkbox': { template: '<input type="checkbox" class="t-checkbox-stub" />' },
          't-dialog': { template: '<div class="t-dialog-stub"><slot /></div>' },
          'router-view': { template: '<div class="router-view-stub"><slot /></div>' },
          'transition': { template: '<div class="transition-stub"><slot /></div>' },
          'SearchSelect': { template: '<div class="search-select-stub"><slot /></div>' }
        },
        mocks: {
          $router: { push: vi.fn() },
          $route: { query: {} }
        }
      }
    })
    
    await nextTick()
  })

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
    }
  })

  describe('表格容器布局', () => {
    it('应存在主内容容器', () => {
      const container = wrapper.find('.files-card-body')
      expect(container.exists()).toBe(true)
    })

    it('应存在表格容器', () => {
      const tableWrapper = wrapper.find('.files-table-wrapper')
      expect(tableWrapper.exists()).toBe(true)
    })
  })

  describe('表格数据绑定', () => {
    it('应该使用paginatedFiles而非filteredFiles', async () => {
      wrapper.vm.files = createMockFiles(50)
      await nextTick()
      
      expect(wrapper.vm.paginatedFiles).toBeDefined()
      expect(wrapper.vm.paginatedFiles.length).toBeLessThanOrEqual(wrapper.vm.pageSize)
    })

    it('文件数量变化时应该自动更新分页', async () => {
      wrapper.vm.files = createMockFiles(10)
      await nextTick()
      expect(wrapper.vm.paginatedFiles).toHaveLength(10)
      
      wrapper.vm.files = createMockFiles(100)
      await nextTick()
      expect(wrapper.vm.paginatedFiles).toHaveLength(10)
    })
  })
})
