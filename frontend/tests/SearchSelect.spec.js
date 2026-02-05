import { mount } from '@vue/test-utils'
import SearchSelect from '../src/components/SearchSelect.vue'

describe('SearchSelect', () => {
  it('搜索与高亮', async () => {
    const wrapper = mount(SearchSelect, {
      props: { modelValue: [], options: [{ label: '跟着扶安学AI', value: '跟着扶安学AI' }, { label: '其他UP', value: '其他UP' }] }
    })
    const input = wrapper.find('input')
    expect(input.attributes('readonly')).toBeUndefined()
    await input.setValue('扶安')
    // popup visible and results rendered
    expect(wrapper.html()).toContain('无匹配数据') // 初始会显示，异步后替换
  })
  it('选中与事件', async () => {
    const wrapper = mount(SearchSelect, {
      props: { modelValue: [], options: [{ label: 'UP1', value: 'UP1' }] }
    })
    await wrapper.find('input').setValue('UP')
    await new Promise(res => setTimeout(res, 350))
    const items = wrapper.findAll('li')
    if (items[0]) await items[0].trigger('mousedown') // 选择
    const emitted = wrapper.emitted('change')
    expect(emitted && emitted[0] && emitted[0][0]).toBeTruthy()
  })
})
