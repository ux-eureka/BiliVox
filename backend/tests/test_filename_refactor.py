import unittest
import os
import shutil
import tempfile
import sys
import re
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from backend.core.bilivox_manager import BiliVoxManager

class TestFilenameRefactoring(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.manager = BiliVoxManager()
        self.manager.output_dir = self.test_dir
        
    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_save_markdown_filename_format(self):
        """Test that saved markdown filenames do NOT contain date or BV ID"""
        video = {
            'title': 'Test Video Title',
            'bv_id': 'BV1234567890',
            'upload_date': '20260101',
            'url': 'http://test.com',
            'uploader': 'TestUP',
            'uid': '1001'
        }
        content = "Markdown content"
        up_name = 'TestUP'
        
        relpath = self.manager._save_markdown(video, content, up_name)
        
        expected_filename = "Test Video Title.md"
        self.assertTrue(relpath.endswith(expected_filename))
        self.assertNotIn("2026-01-01", relpath)
        self.assertNotIn("BV1234567890", relpath)
        
        # Verify content contains frontmatter
        full_path = os.path.join(self.test_dir, relpath)
        with open(full_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
            self.assertIn('bv: BV1234567890', file_content)
            self.assertIn('upload_date: 20260101', file_content)

    def test_get_files_parsing_new_format(self):
        """Test parsing of the new filename format (Name.md)"""
        up_name = 'TestUP'
        up_dir = os.path.join(self.test_dir, up_name)
        os.makedirs(up_dir)
        
        filename = "Test Video Title.md"
        content = """---
title: Test Video Title
bv: BV1234567890
upload_date: 20260101
---
Content
"""
        with open(os.path.join(up_dir, filename), 'w', encoding='utf-8') as f:
            f.write(content)
            
        result = self.manager.get_files()
        files = result['files']
        
        self.assertEqual(len(files), 1)
        file_info = files[0]
        self.assertEqual(file_info['name'], 'Test Video Title')
        self.assertEqual(file_info['bv'], 'BV1234567890')
        self.assertEqual(file_info['date'], '2026-01-01')

    def test_get_files_parsing_old_format_compatibility(self):
        """Test that old filenames (Name_Date_BV.md) are still parsed correctly"""
        up_name = 'TestUP'
        up_dir = os.path.join(self.test_dir, up_name)
        os.makedirs(up_dir)
        
        filename = "Old Video_2025-12-31_BV0987654321.md"
        # File content without frontmatter to test filename parsing fallback
        content = "Old Content"
        with open(os.path.join(up_dir, filename), 'w', encoding='utf-8') as f:
            f.write(content)
            
        result = self.manager.get_files()
        files = result['files']
        
        self.assertEqual(len(files), 1)
        file_info = files[0]
        self.assertEqual(file_info['name'], 'Old Video')
        self.assertEqual(file_info['bv'], 'BV0987654321')
        self.assertEqual(file_info['date'], '2025-12-31')

    def test_date_parsing_edge_cases(self):
        """Test date parsing logic with various inputs"""
        up_name = 'TestUP'
        up_dir = os.path.join(self.test_dir, up_name)
        os.makedirs(up_dir)
        
        # Case 1: Null upload_date from API/File
        filename = "NoDate.md"
        content = """---
title: No Date Video
bv: BV111
---
"""
        with open(os.path.join(up_dir, filename), 'w', encoding='utf-8') as f:
            f.write(content)
            
        result = self.manager.get_files()
        self.assertEqual(result['files'][0]['date'], '未知')

if __name__ == '__main__':
    unittest.main()
