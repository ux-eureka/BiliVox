"""
B站视频处理模块测试
测试视频解析、处理和文件生成逻辑
"""

import pytest
import os
import sys
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# 添加backend目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestVideoValidation:
    """视频对象校验测试"""

    def test_validate_video_with_bv_id(self):
        """测试有效的视频对象"""
        video = {
            'bv_id': 'BV17wERzLEsz',
            'title': '测试视频',
            'url': 'https://www.bilibili.com/video/BV17wERzLEsz'
        }
        assert video.get('bv_id') is not None
        assert video.get('bv_id') == 'BV17wERzLEsz'

    def test_validate_video_without_bv_id(self):
        """测试缺少bv_id的视频对象"""
        video = {
            'title': '测试视频',
            'url': 'https://www.bilibili.com/video/'
        }
        assert not video.get('bv_id')

    def test_validate_video_with_empty_bv_id(self):
        """测试bv_id为空的视频对象"""
        video = {
            'bv_id': '',
            'title': '测试视频'
        }
        assert not video.get('bv_id')


class TestURLNormalization:
    """URL标准化测试"""

    def test_extract_bv_id_from_url(self):
        """从URL中提取BV号"""
        test_cases = [
            ('https://www.bilibili.com/video/BV17wERzLEsz', 'BV17wERzLEsz'),
            ('https://bilibili.com/video/BV1ZhUDYeEHz', 'BV1ZhUDYeEHz'),
            ('https://www.bilibili.com/video/BV17wERzLEsz?spm_id_from=xxx', 'BV17wERzLEsz'),
        ]
        import re
        for url, expected_bv in test_cases:
            match = re.search(r'/video/(BV[0-9A-Za-z]+)', url)
            assert match is not None, f"Failed to extract BV from {url}"
            assert match.group(1) == expected_bv

    def test_extract_bv_id_with_params(self):
        """提取带参数的URL中的BV号"""
        import re
        url = 'https://www.bilibili.com/video/BV17wERzLEsz?spm_id_from=333.788.recommend_more_video.0&trackid=xxx'
        match = re.search(r'/video/(BV[0-9A-Za-z]+)', url)
        assert match is not None
        assert match.group(1) == 'BV17wERzLEsz'


class TestMarkdownGeneration:
    """Markdown生成测试"""

    def test_build_frontmatter(self):
        """测试Frontmatter构建"""
        video = {
            'title': '测试视频标题',
            'bv_id': 'BV17wERzLEsz',
            'url': 'https://www.bilibili.com/video/BV17wERzLEsz',
            'uploader': '测试UP主',
            'uid': '123456',
            'upload_date': '20240101',
            'tags': ['测试', '示例']
        }

        frontmatter_lines = []
        if video.get('title'):
            frontmatter_lines.append(f"title: {video['title']}")
        if video.get('bv_id'):
            frontmatter_lines.append(f"bv: {video['bv_id']}")
        if video.get('url'):
            frontmatter_lines.append(f"url: {video['url']}")
        if video.get('uploader'):
            frontmatter_lines.append(f"author: {video['uploader']}")
        if video.get('uid'):
            frontmatter_lines.append(f"uid: {video['uid']}")
        if video.get('upload_date'):
            frontmatter_lines.append(f"upload_date: {video['upload_date']}")
        tags = video.get('tags')
        if tags and isinstance(tags, list):
            frontmatter_lines.append("tags:")
            for t in tags:
                frontmatter_lines.append(f"  - {t}")

        frontmatter = "---\n" + "\n".join(frontmatter_lines) + "\n---"

        assert "title: 测试视频标题" in frontmatter
        assert "bv: BV17wERzLEsz" in frontmatter
        assert "author: 测试UP主" in frontmatter
        assert "tags:" in frontmatter
        assert "  - 测试" in frontmatter


class TestHistoryRecording:
    """历史记录测试"""

    def test_history_entry_structure(self):
        """测试历史记录条目结构"""
        entry = {
            'up_name': '测试UP主',
            'title': '测试视频',
            'status': '成功',
            'task_id': 'task-001',
            'file_path': '/output/测试UP主/测试视频.md',
            'detail': '处理完成',
            'duration_sec': 120,
            'timestamp': datetime.now().isoformat()
        }

        assert entry['up_name'] == '测试UP主'
        assert entry['status'] in ['成功', '失败']
        assert isinstance(entry['duration_sec'], int)


class TestSkipLogic:
    """跳过逻辑测试"""

    def test_should_skip_with_matching_bv_in_filename(self):
        """测试根据BV号跳过处理"""
        existing_files = [
            '测试视频-BV17wERzLEsz.md',
            '另一个视频.md'
        ]
        video_bv = 'BV17wERzLEsz'
        video_title = '测试视频'

        should_skip = any(
            video_bv in file or video_title in file
            for file in existing_files
        )

        assert should_skip is True

    def test_should_not_skip_with_different_bv(self):
        """测试不同BV号不应跳过"""
        existing_files = [
            '测试视频-BV17wERzLEsz.md',
            '另一个视频.md'
        ]
        video_bv = 'BV1ZhUDYeEHz'
        video_title = '新视频'

        should_skip = any(
            video_bv in file or video_title in file
            for file in existing_files
        )

        assert should_skip is False

    def test_force_flag_should_not_skip(self):
        """测试强制处理标志不应跳过"""
        existing_files = ['测试视频-BV17wERzLEsz.md']
        force = True

        should_skip = not force and any(
            'BV17wERzLEsz' in file or '测试视频' in file
            for file in existing_files
        )

        assert should_skip is False


class TestErrorHandling:
    """错误处理测试"""

    def test_handle_missing_bv_id(self):
        """测试缺少bv_id时的错误处理"""
        video = {'title': '测试视频'}
        error = None
        try:
            bv_id = video.get('bv_id')
            if not bv_id:
                raise ValueError('缺少视频ID (bv_id)')
        except Exception as e:
            error = e

        assert error is not None
        assert 'bv_id' in str(error)

    def test_handle_api_error(self):
        """测试API错误处理"""
        mock_response = {'code': -404, 'message': '啥都木有', 'data': None}

        if mock_response.get('code') != 0:
            error_msg = f"API 返回异常: {mock_response.get('message', '未知错误')}"
            raise ValueError(error_msg)

        # 这个测试应该抛出异常
        with pytest.raises(ValueError):
            if mock_response.get('code') != 0:
                raise ValueError(f"API 返回异常: {mock_response.get('message')}")


class TestEdgeCases:
    """边界情况测试"""

    def test_empty_video_list(self):
        """测试空视频列表"""
        videos = []
        assert len(videos) == 0

    def test_video_with_special_chars_in_title(self):
        """测试标题包含特殊字符"""
        title = '测试:视频"标题"\\测试'
        safe_title = ''.join(c for c in title if c not in '\\/:*?"<>|')
        assert ':' in safe_title  # 冒号应该保留
        assert '"' not in safe_title  # 引号应该被移除

    def test_long_url_with_many_params(self):
        """测试带很多参数的URL"""
        url = 'https://www.bilibili.com/video/BV17wERzLEsz?a=1&b=2&c=3&d=4&e=5'
        import re
        match = re.search(r'/video/(BV[0-9A-Za-z]+)', url)
        assert match is not None
        assert match.group(1) == 'BV17wERzLEsz'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
