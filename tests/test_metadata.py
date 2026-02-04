import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.downloader import BiliDownloader

class TestMetadataExtraction(unittest.TestCase):
    def setUp(self):
        self.config = {
            'download': {
                'temp_dir': 'temp',
                'headers': {'User-Agent': 'Test'},
                'audio_format': 'm4a'
            }
        }
        self.downloader = BiliDownloader(self.config)

    @patch('core.downloader.urlopen')
    def test_get_video_meta_success(self, mock_urlopen):
        # Mock successful response
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "code": 0,
            "data": {
                "title": "Test Video",
                "duration": 100,
                "owner": {
                    "name": "TestUP",
                    "mid": 12345
                },
                "pubdate": 1600000000
            }
        }).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        meta = self.downloader.get_video_meta("BV1xx411c7mD")
        
        self.assertEqual(meta['owner_name'], "TestUP")
        self.assertEqual(meta['uploader'], "TestUP")
        self.assertEqual(meta['uid'], "12345")
        self.assertIsNotNone(meta['upload_date'])

    @patch('core.downloader.urlopen')
    def test_get_video_meta_missing_owner(self, mock_urlopen):
        # Mock response with missing owner info (edge case)
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "code": 0,
            "data": {
                "title": "Test Video",
                "duration": 100,
                # owner is missing or null
                "owner": None
            }
        }).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        meta = self.downloader.get_video_meta("BV1xx411c7mD")
        
        self.assertIsNone(meta['owner_name'])
        self.assertEqual(meta['uid'], "")

    @patch('core.downloader.urlopen')
    def test_get_video_meta_api_failure(self, mock_urlopen):
        # Mock API failure
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "code": -404,
            "message": "Not Found"
        }).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        with self.assertRaises(ValueError):
            self.downloader.get_video_meta("BV1xx411c7mD")

if __name__ == '__main__':
    unittest.main()
