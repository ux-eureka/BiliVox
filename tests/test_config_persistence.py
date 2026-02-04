import unittest
import os
import sys
import shutil
import tempfile
import yaml
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.bilivox_manager import BiliVoxManager

class TestConfigPersistence(unittest.TestCase):
    def setUp(self):
        # Create temporary directory for config
        self.test_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.test_dir, 'config.yaml')
        self.history_path = os.path.join(self.test_dir, 'history.json')
        
        # Patch BiliVoxManager to use temp paths
        self.original_init = BiliVoxManager.__init__
        def mocked_init(manager_self):
            manager_self.repo_root = self.test_dir
            manager_self.config_path = self.config_path
            manager_self.history_path = self.history_path
            manager_self.output_dir = os.path.join(self.test_dir, 'output')
            manager_self.monitor_state_path = os.path.join(self.test_dir, 'monitor_state.json')
            manager_self._monitor_lock = None # Mock lock not needed for basic config test
            manager_self.logs = []
            manager_self.history = []
            
            # Create dummy config
            with open(self.config_path, 'w') as f:
                yaml.dump({'llm': {'enabled': True}}, f)
                
            manager_self.load_config()
            # Skip heavy init
            manager_self.downloader = None
            manager_self.transcriber = None
            manager_self.llm_processor = None
            manager_self.bibigpt_client = None
            manager_self.status = '空闲'
            manager_self.progress = 0
            manager_self.stop_event = None
            manager_self.current_task_id = None
            manager_self.current_up_name = None
            manager_self.current_title = None

        BiliVoxManager.__init__ = mocked_init
        self.manager = BiliVoxManager()

    def tearDown(self):
        # Restore init
        BiliVoxManager.__init__ = self.original_init
        shutil.rmtree(self.test_dir)

    def test_preset_id_persistence(self):
        # 1. Initial state: preset_id should be None (default)
        config = self.manager.get_config()
        self.assertIsNone(config['llm'].get('preset_id'))

        # 2. Update config with a preset_id
        new_config = {
            'llm': {
                'preset_id': 'test-preset-123',
                'api_base_url': 'https://test.com',
                'model_name': 'test-model'
            }
        }
        self.manager.update_config(new_config)

        # 3. Verify in memory
        current_config = self.manager.get_config()
        self.assertEqual(current_config['llm']['preset_id'], 'test-preset-123')
        self.assertEqual(current_config['llm']['api_base_url'], 'https://test.com')

        # 4. Verify on disk
        with open(self.config_path, 'r', encoding='utf-8') as f:
            disk_config = yaml.safe_load(f)
        self.assertEqual(disk_config['llm']['preset_id'], 'test-preset-123')

        # 5. Reload manager (simulate restart)
        self.manager.load_config()
        reloaded_config = self.manager.get_config()
        self.assertEqual(reloaded_config['llm']['preset_id'], 'test-preset-123')

    def test_preset_fallback(self):
        # Test that if preset_id is missing, we don't crash
        new_config = {
            'llm': {
                'api_base_url': 'https://custom.com'
                # No preset_id provided
            }
        }
        self.manager.update_config(new_config)
        
        current_config = self.manager.get_config()
        # Should remain what it was or be updated? 
        # update_config uses dict.update(), so existing keys persist unless overwritten
        # If we want to clear preset_id, we must send preset_id: None
        
        # Let's clear it explicitly
        self.manager.update_config({'llm': {'preset_id': None}})
        self.assertIsNone(self.manager.get_config()['llm']['preset_id'])

if __name__ == '__main__':
    unittest.main()