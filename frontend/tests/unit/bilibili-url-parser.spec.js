/**
 * B站视频链接解析测试
 * 测试各种B站链接格式的解析
 */

import { describe, it, expect } from 'vitest'

const extractBilibiliVideoItems = (text) => {
  const normalized = String(text || '')
  const items = []

  const videoUrlRegex = /https?:\/\/(?:www\.)?bilibili\.com\/video\/(BV[0-9A-Za-z]+)[^]*/g
  let match
  while ((match = videoUrlRegex.exec(normalized)) !== null) {
    const bvId = match[1]
    const fullUrl = match[0].split('#')[0]
    if (!items.find(i => i.bvId === bvId)) {
      items.push({ bvId, url: fullUrl })
    }
  }

  const bvOnlyRegex = /\b(BV[0-9A-Za-z]{8,})\b/g
  while ((match = bvOnlyRegex.exec(normalized)) !== null) {
    const bvId = match[1]
    const url = `https://www.bilibili.com/video/${bvId}`
    if (!items.find(i => i.bvId === bvId)) {
      items.push({ bvId, url })
    }
  }

  return items
}

describe('B站视频链接解析', () => {
  describe('标准链接格式', () => {
    it('应该正确解析标准视频链接', () => {
      const result = extractBilibiliVideoItems('https://www.bilibili.com/video/BV1ZhUDYeEHz')
      expect(result).toHaveLength(1)
      expect(result[0].bvId).toBe('BV1ZhUDYeEHz')
      expect(result[0].url).toBe('https://www.bilibili.com/video/BV1ZhUDYeEHz')
    })

    it('应该正确解析无www的视频链接', () => {
      const result = extractBilibiliVideoItems('https://bilibili.com/video/BV17wERzLEsz')
      expect(result).toHaveLength(1)
      expect(result[0].bvId).toBe('BV17wERzLEsz')
    })

    it('应该正确解析http链接', () => {
      const result = extractBilibiliVideoItems('http://www.bilibili.com/video/BV1RiUDYcErx')
      expect(result).toHaveLength(1)
      expect(result[0].bvId).toBe('BV1RiUDYcErx')
    })
  })

  describe('带参数的链接', () => {
    it('应该正确解析带spm参数的链接', () => {
      const url = 'https://www.bilibili.com/video/BV17wERzLEsz?spm_id_from=333.788.recommend_more_video.0'
      const result = extractBilibiliVideoItems(url)
      expect(result).toHaveLength(1)
      expect(result[0].bvId).toBe('BV17wERzLEsz')
      expect(result[0].url).toContain('BV17wERzLEsz')
      expect(result[0].url).toContain('spm_id_from')
    })

    it('应该正确解析复杂参数的链接', () => {
      const url = 'https://www.bilibili.com/video/BV17wERzLEsz?spm_id_from=333.788.recommend_more_video.0&trackid=web_related_0.router-related-2481894-kljzp.1770373222347.789&vd_source=5456f3b985758627c78c262fb6501532'
      const result = extractBilibiliVideoItems(url)
      expect(result).toHaveLength(1)
      expect(result[0].bvId).toBe('BV17wERzLEsz')
      expect(result[0].url).toContain('spm_id_from')
      expect(result[0].url).toContain('trackid')
    })

    it('应该正确解析带锚点的链接', () => {
      const result = extractBilibiliVideoItems('https://www.bilibili.com/video/BV1KhkxBpEP4#comment')
      expect(result).toHaveLength(1)
      expect(result[0].bvId).toBe('BV1KhkxBpEP4')
      expect(result[0].url).not.toContain('#')
    })
  })

  describe('纯BV号格式', () => {
    it('应该正确解析纯BV号', () => {
      const result = extractBilibiliVideoItems('BV1xx411s7x1')
      expect(result).toHaveLength(1)
      expect(result[0].bvId).toBe('BV1xx411s7x1')
      expect(result[0].url).toBe('https://www.bilibili.com/video/BV1xx411s7x1')
    })

    it('应该正确解析文本中的BV号', () => {
      const text = '这是一个视频BV1xx411s7x1的测试'
      const result = extractBilibiliVideoItems(text)
      expect(result).toHaveLength(1)
      expect(result[0].bvId).toBe('BV1xx411s7x1')
    })
  })

  describe('混合格式', () => {
    it('应该正确解析多个链接', () => {
      const text = '视频1: https://www.bilibili.com/video/BV1ZhUDYeEHz 和视频2: https://bilibili.com/video/BV17wERzLEsz'
      const result = extractBilibiliVideoItems(text)
      expect(result).toHaveLength(2)
      expect(result.map(i => i.bvId)).toContain('BV1ZhUDYeEHz')
      expect(result.map(i => i.bvId)).toContain('BV17wERzLEsz')
    })

    it('应该去重重复的链接', () => {
      const text = 'BV1ZhUDYeEHz https://www.bilibili.com/video/BV1ZhUDYeEHz'
      const result = extractBilibiliVideoItems(text)
      expect(result).toHaveLength(1)
    })

    it('应该正确解析混合链接和BV号', () => {
      const text = '请处理这个视频https://www.bilibili.com/video/BV1ZhUDYeEHz?spm_id_from=xxx，还有BV17wERzLEsz'
      const result = extractBilibiliVideoItems(text)
      expect(result).toHaveLength(2)
    })
  })

  describe('边界情况', () => {
    it('应该处理空字符串', () => {
      const result = extractBilibiliVideoItems('')
      expect(result).toHaveLength(0)
    })

    it('应该处理null输入', () => {
      const result = extractBilibiliVideoItems(null)
      expect(result).toHaveLength(0)
    })

    it('应该处理undefined输入', () => {
      const result = extractBilibiliVideoItems(undefined)
      expect(result).toHaveLength(0)
    })

    it('应该处理无效输入', () => {
      const result = extractBilibiliVideoItems('这不是一个有效的链接')
      expect(result).toHaveLength(0)
    })

    it('应该处理错误的BV号格式', () => {
      const result = extractBilibiliVideoItems('https://www.bilibili.com/video/BV1X')
      expect(result).toHaveLength(0)
    })
  })

  describe('特殊格式', () => {
    it('应该正确解析长BV号', () => {
      const result = extractBilibiliVideoItems('BV1xx411s7x1xx411s7x1')
      expect(result).toHaveLength(1)
      expect(result[0].bvId).toBe('BV1xx411s7x1xx411s7x1')
    })

    it('应该正确处理链接末尾的空格', () => {
      const result = extractBilibiliVideoItems('https://www.bilibili.com/video/BV1ZhUDYeEHz ')
      expect(result).toHaveLength(1)
      expect(result[0].bvId).toBe('BV1ZhUDYeEHz')
    })
  })
})

describe('URL验证', () => {
  const testUrls = [
    'https://www.bilibili.com/video/BV17wERzLEsz?spm_id_from=333.788.recommend_more_video.0',
    'https://www.bilibili.com/video/BV1ZhUDYeEHz',
    'https://bilibili.com/video/BV1RiUDYcErx',
    'http://www.bilibili.com/video/BV1KhkxBpEP4',
    'BV1xx411s7x1',
    'https://www.bilibili.com/video/BV17wERzLEsz?utm_source=test&utm_medium=social'
  ]

  testUrls.forEach((url, index) => {
    it(`测试用例 ${index + 1}: ${url}`, () => {
      const result = extractBilibiliVideoItems(url)
      expect(result.length).toBeGreaterThanOrEqual(1)
      expect(result[0].bvId).toMatch(/^BV[0-9A-Za-z]{8,}$/)
    })
  })
})
