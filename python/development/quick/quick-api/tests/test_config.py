import unittest
import os
from app.core.config import get_connection_config, get_request_config, get_input_path, get_output_path

class TestConfig(unittest.TestCase):
    """設定読み込み機能のテスト"""

    def test_get_connection_config(self):
        """接続設定の読み込みテスト"""
        config = get_connection_config()
        self.assertIsNotNone(config)
        self.assertIn('api', config)
        self.assertIn('base_url', config['api'])
        self.assertIn('access_key', config['api'])
        self.assertIn('format', config['api'])

    def test_get_request_config(self):
        """リクエスト設定の読み込みテスト"""
        config = get_request_config()
        self.assertIsNotNone(config)
        self.assertIn('input', config)
        self.assertIn('output', config)
        self.assertIn('base_dir', config['input'])
        self.assertIn('daily_dir', config['input'])
        self.assertIn('spot_dir', config['input'])
        self.assertIn('request_file', config['input'])

    def test_get_input_path_daily(self):
        """日次実行の入力パス取得テスト"""
        path = get_input_path('daily')
        self.assertTrue(isinstance(path, str))
        self.assertIn('daily', path)
        self.assertIn('requests.yml', path)

    def test_get_input_path_spot(self):
        """スポット実行の入力パス取得テスト"""
        test_date = "20231208"
        path = get_input_path('spot', test_date)
        self.assertTrue(isinstance(path, str))
        self.assertIn('spot', path)
        self.assertIn(test_date, path)
        self.assertIn('requests.yml', path)

    def test_get_input_path_invalid_mode(self):
        """無効なモードでの入力パス取得テスト"""
        with self.assertRaises(ValueError):
            get_input_path('invalid')

    def test_get_input_path_spot_without_date(self):
        """日付なしでのスポット実行入力パス取得テスト"""
        with self.assertRaises(ValueError):
            get_input_path('spot')

    def test_get_output_path(self):
        """出力パス取得テスト"""
        test_date = "20231208"
        
        # 日次実行の出力パス
        daily_path = get_output_path('daily', test_date)
        self.assertTrue(isinstance(daily_path, str))
        self.assertIn('daily', daily_path)
        self.assertIn(test_date, daily_path)
        self.assertIn('data', daily_path)
        
        # スポット実行の出力パス
        spot_path = get_output_path('spot', test_date)
        self.assertTrue(isinstance(spot_path, str))
        self.assertIn('spot', spot_path)
        self.assertIn(test_date, spot_path)
        self.assertIn('data', spot_path)

    def test_get_output_path_invalid_mode(self):
        """無効なモードでの出力パス取得テスト"""
        test_date = "20231208"
        with self.assertRaises(ValueError):
            get_output_path('invalid', test_date)