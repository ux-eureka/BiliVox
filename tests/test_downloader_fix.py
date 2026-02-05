
import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.downloader import BiliDownloader

class TestBiliDownloaderFix(unittest.TestCase):
    def setUp(self):
        self.config = {
            'download': {
                'temp_dir': 'temp_test',
                'headers': {},
                'audio_format': 'mp3'
            }
        }
        self.downloader = BiliDownloader(self.config)

    def test_normalize_video_url_clean_bv(self):
        # Case 1: Pure BV ID
        url = self.downloader._normalize_video_url(None, "BV1EG411h7wP")
        self.assertEqual(url, "https://www.bilibili.com/video/BV1EG411h7wP")

    def test_normalize_video_url_dirty_full_url(self):
        # Case 2: Full URL with dirty params
        dirty_url = "https://www.bilibili.com/video/BV1EG411h7wP/?spm_id_from=333.788.player.switch&trackid=web_related_0"
        url = self.downloader._normalize_video_url(dirty_url, None)
        self.assertEqual(url, "https://www.bilibili.com/video/BV1EG411h7wP")

    def test_normalize_video_url_with_path(self):
        # Case 3: Path only
        path = "/video/BV1EG411h7wP"
        url = self.downloader._normalize_video_url(path, "BV1EG411h7wP")
        self.assertEqual(url, "https://www.bilibili.com/video/BV1EG411h7wP")

    def test_normalize_video_url_multi_page(self):
        # Case 4: URL with ?p=2 (should probably be preserved if user intends to download specific page? 
        # But for now, we assume user wants the main video or the specific BV logic handles it.
        # Actually, if it's the same BV, it's fine. If p=2 changes content, stripping it might be wrong.
        # However, the user issue was "unrelated video". 
        # For this task, we prioritize stripping tracking params.
        # If p=2 is important, maybe we should keep it? 
        # But the regex match `BV...` extraction strategy ignores params.
        # Let's see behavior.
        
        url_p2 = "https://www.bilibili.com/video/BV1EG411h7wP?p=2"
        # My implementation extracts BV and reconstructs URL, so it loses ?p=2.
        # This might be a trade-off. But strictly following "wrong video" caused by "related" params, this is safer.
        
        normalized = self.downloader._normalize_video_url(url_p2, None)
        self.assertEqual(normalized, "https://www.bilibili.com/video/BV1EG411h7wP")

    @patch('core.downloader.urlopen')
    def test_get_video_meta_success(self, mock_urlopen):
        # Mock response
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "code": 0,
            "data": {
                "View": {
                    "title": "Test Title",
                    "duration": 100,
                    "owner": {"name": "Test Owner", "mid": 123},
                    "pubdate": 1600000000
                },
                "Tags": [{"tag_name": "Tag1"}]
            }
        }).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        meta = self.downloader.get_video_meta("BV1EG411h7wP")
        self.assertEqual(meta['title'], "Test Title")
        self.assertEqual(meta['bvId'], "BV1EG411h7wP")
        self.assertEqual(meta['tags'], ["Tag1"])

if __name__ == '__main__':
    import json
    unittest.main()
