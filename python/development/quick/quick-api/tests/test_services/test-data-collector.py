import unittest
from unittest.mock import patch, Mock
import os
import shutil
from datetime import datetime
from app.api.client import QuickApiClient
from app.services.data_collector import DataCollector

class TestDataCollector(unittest.TestCase):
    """DataCollectorのテスト"""

    def setUp(self):
        """テストの前準備"""
        self.mock_client = Mock(spec=QuickApiClient)
        self.collector = DataCollector(self.mock_client)
        
        # テスト用の出力ディレクトリを作成
        self.test_output_dir = os.path.join('output', 'test')
        os.makedirs(os.path.join(self.test_output_dir, 'daily'), exist_ok=True)
        os.makedirs(os.path.join(self.test_output_dir, 'spot'), exist_ok=True)

        # データコレクターの出力先を変更するパッチ
        self.output_dir_patcher = patch.object(
            self.collector,
            '_get_output_base_dir',
            return_value=self.test_output_dir
        )
        self.output_dir_patcher.start()

    def tearDown(self):
        """テスト後のクリーンアップ"""
        self.output_dir_patcher.stop()
        # テスト用の出力ディレクトリのクリーンアップ
        if os.path.exists(self.test_output_dir):
            shutil.rmtree(self.test_output_dir)

    def test_execute_daily_requests_success(self):
        """日次リクエスト実行成功のテスト"""
        self.mock_client.request_data.return_value = ('test_file.csv', None)
        results = self.collector.execute_daily_requests()
        
        self.assertIn('quote_index', results['success'])
        self.assertEqual(len(results['failure']), 0)
        self.mock_client.request_data.assert_called_once()

    def test_execute_daily_requests_failure(self):
        """日次リクエスト実行失敗のテスト"""
        self.mock_client.request_data.side_effect = Exception('テストエラー')
        results = self.collector.execute_daily_requests()
        
        self.assertIn('quote_index', results['failure'])
        self.assertEqual(len(results['success']), 0)

    def test_create_execution_report(self):
        """実行レポート作成のテスト"""
        self.collector.results = {
            'success': ['test1', 'test2'],
            'failure': ['test3']
        }
        
        execution_date = datetime.now().strftime("%Y%m%d")
        report_dir = os.path.join(self.test_output_dir, "daily", execution_date, "reports")
        os.makedirs(report_dir, exist_ok=True)
        
        self.collector.create_execution_report(mode='daily')
        
        report_files = os.listdir(report_dir)
        self.assertTrue(any(file.startswith('execution_report_') for file in report_files))