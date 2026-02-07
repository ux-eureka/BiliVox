import { mount } from '@vue/test-utils'
import { describe, it, expect, beforeEach } from 'vitest'
import { nextTick } from 'vue'
import Files from '../../src/views/Files.vue'

const createMockFiles = (count) => {
  return Array.from({ length: count }, (_, i) => ({
    id: `file-${i}`,
    name: `测试文件 ${i + 1}.md`,
    bv: `BV${String(i + 1).padStart(10, '0')}`,
    date: '2024-01-01',
    up: 'UP主A',
    path: `/files/test-${i + 1}.md`,
    modifiedTs: Date.now()
  }))
}

describe('Files.vue 分页边界', () => {
  let wrapper

  beforeEach(async () => {
    wrapper = mount(Files, {
      global: {
        stubs: {
          't-card': { template: '<div><slot /></div>' },
          't-table': { template: '<div><slot /></div>' },
          't-pagination': { template: '<div />' },
          't-input': { template: '<input />' },
          't-button': { template: '<button><slot /></button>' },
          't-tag': { template: '<span><slot /></span>' },
          't-icon': { template: '<span />' },
          't-select': { template: '<select><slot /></select>' },
          't-option': { template: '<option><slot /></option>' },
          't-checkbox': { template: '<input type=\"checkbox\" />' },
          't-dialog': { template: '<div><slot /></div>' },
          'router-view': { template: '<div><slot /></div>' },
          'transition': { template: '<div><slot /></div>' },
          'SearchSelect': { template: '<div><slot /></div>' }
        }
      }
    })
    await nextTick()
  })

  it('页码越界时应约束到最大页', async () => {
    wrapper.vm.files = createMockFiles(12)
    wrapper.vm.pageSize = 10
    await nextTick()
    wrapper.vm.onPageChange({ current: 99 })
    const maxPage = Math.ceil(wrapper.vm.filteredFiles.length / wrapper.vm.pageSize)
    expect(wrapper.vm.currentPage).toBe(maxPage)
  })

  it('页码小于1时应重置为1', async () => {
    wrapper.vm.files = createMockFiles(12)
    wrapper.vm.pageSize = 10
    await nextTick()
    wrapper.vm.onPageChange(0)
    expect(wrapper.vm.currentPage).toBe(1)
  })

  it('修改每页数量后应重置到第一页', async () => {
    wrapper.vm.files = createMockFiles(100)
    wrapper.vm.currentPage = 3
    await nextTick()
    wrapper.vm.onPageSizeChange({ pageSize: 20 })
    expect(wrapper.vm.pageSize).toBe(20)
    expect(wrapper.vm.currentPage).toBe(1)
  })

  it('分页数据应按当前页正确切片', async () => {
    wrapper.vm.files = createMockFiles(25)
    await nextTick()
    expect(wrapper.vm.paginatedFiles).toHaveLength(10)
    wrapper.vm.onPageChange({ current: 3 })
    await nextTick()
    expect(wrapper.vm.paginatedFiles).toHaveLength(5)
  })
})
