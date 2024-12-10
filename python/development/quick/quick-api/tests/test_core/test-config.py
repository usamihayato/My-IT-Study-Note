import unittest
from app.core.config import get_connection_config

class TestConfig(unittest.TestCase):
    """設定読み込み機能のテスト"""

    def test_get_connection_config(self):
        """接続設定の読み込みテスト"""
        config = get_connection_config()
        self.assertIsNotNone(config)
        self.assertIn('api', config)
        self.assertIn('base_url', config['api'])
        self.assertIn('access_key', config['api'])
        # 必須項目の存在確認
        self.assertIn('format', config['api'])