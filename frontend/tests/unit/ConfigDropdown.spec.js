
import { mount } from '@vue/test-utils'
import { describe, it, expect, vi } from 'vitest'
import Config from '../../src/views/Config.vue'
import { createTestingPinia } from '@pinia/testing'

// Mock vue-router
vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: vi.fn()
  }),
  useRoute: () => ({
    query: {}
  })
}))

// Mock http module
vi.mock('../../src/api/http', () => ({
  http: {
    get: vi.fn().mockResolvedValue({ data: [] }),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn()
  },
  API_KEY_STORAGE_KEY: 'bilivox_api_key'
}))

// Mock task store directly since useTaskStore is called in setup
vi.mock('../../src/store/task', () => ({
  useTaskStore: vi.fn(() => ({
    tasks: [],
    addTasksFromUpVideos: vi.fn()
  }))
}))

describe('Config.vue Dropdown', () => {
  it('renders preset options correctly via t-option slots', async () => {
    const wrapper = mount(Config, {
      global: {
        plugins: [
          createTestingPinia({
            createSpy: vi.fn,
          }),
        ],
        stubs: {
          // Stub t-select to render default slot (containing t-options)
          't-select': {
            template: '<div class="t-select-stub"><slot /></div>'
          },
          // Stub t-option to render its slot content
          't-option': {
            props: ['label', 'value'],
            template: '<div class="t-option-stub"><slot /></div>'
          },
          // Stub other UI components
          't-card': { template: '<div><slot /></div>' },
          't-button': true,
          't-icon': true,
          't-tabs': { template: '<div><slot /></div>' },
          't-tab-panel': { template: '<div><slot /></div>' },
          't-row': { template: '<div><slot /></div>' },
          't-col': { template: '<div><slot /></div>' },
          't-avatar': true,
          't-form': { template: '<div><slot /></div>' },
          't-form-item': { template: '<div><slot /></div>' },
          't-radio-group': true,
          't-radio-button': true,
          't-input': true,
          't-slider': true,
          't-divider': true,
          't-dialog': true,
          't-popconfirm': true,
          't-textarea': true,
          't-input-number': true,
          't-tag': true,
          't-select-input': true
        },
        mocks: {
          $router: { push: vi.fn() },
          $route: { query: {} }
        }
      }
    })

    // 1. Manually inject presets data
    wrapper.vm.presets = [
      { 
        id: 'p1', 
        name: 'DeepSeek V3 Test', 
        model_name: 'deepseek-v3', 
        api_base_url: 'https://api.test' 
      }
    ]
    
    // Trigger update
    await wrapper.vm.$nextTick()
    
    // Check if t-select received the options
    const select = wrapper.findComponent({ name: 't-select' })
    
    // Check DOM to verify t-option rendering
    const renderedOptions = wrapper.findAll('.t-option-stub')
    expect(renderedOptions.length).toBeGreaterThan(0)
    
    // Verify the text content of the options
    const textContents = renderedOptions.map(w => w.text())
    console.log('Rendered options text:', textContents)
    
    const validTexts = textContents.filter(t => t.trim() !== '')
    const targetOption = validTexts.find(t => t.includes('DeepSeek V3 Test'))
    expect(targetOption).toBeTruthy()
    expect(targetOption).toContain('deepseek-v3')
    
    // Assertions for data structure (The Fix)
    const options = wrapper.vm.presetOptions
    expect(options).toHaveLength(1)
    expect(options[0].label).toContain('DeepSeek V3 Test')
    expect(options[0].title).toBe('DeepSeek V3 Test')
    expect(options[0]).toHaveProperty('rawPreset')
    expect(options[0]).not.toHaveProperty('content') // CRITICAL: verify collision avoidance
    
    // 2. Test with dirty data (name is an object)
    // Note: To properly trigger reactivity in this test setup with computed properties, 
    // we need to make sure presets is treated as reactive.
    // In the component, presets is a ref([]).
    // In the test, wrapper.vm.presets accesses that ref's value.
    
    // Let's try resetting it completely
    wrapper.vm.presets = []
    await wrapper.vm.$nextTick()
    
    wrapper.vm.presets = [
      { 
        id: 'p2', 
        name: { some: 'object' }, // Dirty data
        model_name: 'dirty-model', 
        api_base_url: 'https://api.dirty' 
      }
    ]
    await wrapper.vm.$nextTick()
    
    // Check vm.presetOptions again
    const dirtyOptions = wrapper.vm.presetOptions
    expect(dirtyOptions).toHaveLength(1)
    const dirtyOpt = dirtyOptions[0]
    
    // Label should be stringified
    expect(dirtyOpt.label).toContain('{"some":"object"}')
    expect(dirtyOpt.title).toBe('{"some":"object"}')
    expect(dirtyOpt.label).not.toBe('[object Object]')
    
    // Structure check
    expect(dirtyOpt.rawPreset.model_name).toBe('dirty-model')
  })
})
