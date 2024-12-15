import unittest
from unittest.mock import patch, Mock, call
import os
import shutil
import yaml
from datetime import datetime
from app.api.client import QuickApiClient
from app.services.data_collector import DataCollector
from app.core.config import get_connection_config, get_request_config

class TestDataCollector(unittest.TestCase):
    """DataCollectorのテスト"""

    @classmethod
    def setUpClass(cls):
        """テストクラス全体の前準備"""
        cls.connection_config = get_connection_config()
        cls.request_config = get_request_config()

    def setUp(self):
        """テストの前準備"""
        # 実際の設定を読み込む
        self.original_config = get_request_config()
        
        # テスト用の出力ディレクトリ
        self.test_output_dir = os.path.join('output', 'test')
        os.makedirs(self.test_output_dir, exist_ok=True)
        
        # テスト用の設定は実際の設定をベースに出力パスのみ変更
        self.test_config = self.original_config.copy()
        self.test_config['output'] = {
            'base_dir': self.test_output_dir,
            'daily_dir': 'daily',
            'spot_dir': 'spot'
        }
        
        # モックの設定
        self.mock_client = Mock(spec=QuickApiClient)
        self.collector = DataCollector(self.mock_client)

    def tearDown(self):
        """テスト後のクリーンアップ"""
        if os.path.exists(self.test_output_dir):
            shutil.rmtree(self.test_output_dir)

    def _load_existing_request_file(self, mode: str, date: str = None) -> dict:
        """既存のリクエスト定義ファイルを読み込む"""
        # ファイルパスの構築
        if mode == 'daily':
            file_path = os.path.join(
                self.request_config['input']['base_dir'],
                self.request_config['input']['daily_dir'],
                self.request_config['input']['request_file']
            )
        else:
            file_path = os.path.join(
                self.request_config['input']['base_dir'],
                self.request_config['input']['spot_dir'],
                date,
                self.request_config['input']['request_file']
            )

        # ファイルの存在確認
        if not os.path.exists(file_path):
            self.skipTest(f"定義ファイルが存在しません: {file_path}")

        # ファイルの読み込み
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def test_execute_daily_requests_success(self):
        """日次実行の正常系テスト"""
        # 1. 既存の定義ファイルを読み込む
        definition = self._load_existing_request_file('daily')
        
        # デバッグ出力を追加
        print("\nDaily requests definition:")
        enabled_requests = []
        print("\nEnabled requests:")
        for name, config in definition['requests'].items():
            enabled = config.get('enabled', True)
            print(f"- {name}: enabled = {enabled}")
            if enabled:
                enabled_requests.append(name)
        print(f"\nTotal enabled requests: {len(enabled_requests)}")
        print(f"Enabled request list: {enabled_requests}")
        
        # 2. モック設定
        self.mock_client.request_data.return_value = ('test_output.csv', None)
        
        # 3. テスト実行
        with patch('app.core.config.get_request_config', return_value=self.test_config):
            results = self.collector.execute_daily_requests()
            
            # デバッグ出力を追加
            print("\nExecution results:")
            print(f"Success count: {len(results['success'])}")
            print(f"Success list: {results['success']}")
            print(f"API call count: {self.mock_client.request_data.call_count}")
            
            # 4. 結果の検証
            self.assertEqual(
                self.mock_client.request_data.call_count,
                len(enabled_requests),
                f"有効なリクエスト数とAPI呼び出し回数が一致すること\n"
                f"Expected: {len(enabled_requests)}, Got: {self.mock_client.request_data.call_count}"
            )
            
            self.assertEqual(
                len(results['success']),
                len(enabled_requests),
                f"すべての有効なリクエストが成功すること\n"
                f"Expected: {len(enabled_requests)}, Got: {len(results['success'])}\n"
                f"Expected list: {enabled_requests}\n"
                f"Actual list: {results['success']}"
            )

    def test_execute_spot_requests_with_paging(self):
        """スポット実行でのページング処理テスト"""
        # 1. テスト用の日付ディレクトリを探す
        spot_dir = os.path.join(
            self.request_config['input']['base_dir'],
            self.request_config['input']['spot_dir']
        )
        
        if not os.path.exists(spot_dir):
            self.skipTest("スポット実行ディレクトリが存在しません")

        test_dates = [d for d in os.listdir(spot_dir) 
                     if os.path.isdir(os.path.join(spot_dir, d))]
        if not test_dates:
            self.skipTest("スポット実行の定義ディレクトリが存在しません")

        # 2. 最新の定義ファイルを使用
        test_date = sorted(test_dates)[-1]
        definition = self._load_existing_request_file('spot', test_date)

        # 3. ページング対応のエンドポイントを確認
        paging_endpoints = [name for name, config in definition['requests'].items() 
                          if name in ['foreign_fund', 'fund', 'quote_stock']]
        if not paging_endpoints:
            self.skipTest("ページング対応のエンドポイントが定義されていません")

        # 4. ページング処理のシミュレーション
        self.mock_client.request_data.side_effect = [
            ('output1.csv', 'NEXT_1'),
            ('output2.csv', 'NEXT_2'),
            ('output3.csv', None)
        ]

        # 5. テスト実行と検証
        with patch('app.core.config.get_request_config', return_value=self.test_config):
            results = self.collector.execute_spot_requests(test_date)
            self.assertTrue(
                self.mock_client.request_data.call_count >= 3,
                "ページング処理による複数回のAPI呼び出しが行われること"
            )
            self.assertGreater(len(results['success']), 0,
                "少なくとも1つのリクエストが成功すること"
            )

    # def test_create_execution_report(self):
    #     """実行レポート作成のテスト"""
    #     # 1. テストデータの準備
    #     test_date = datetime.now().strftime("%Y%m%d")
    #     self.collector.results = {
    #         "success": ["quote_index", "quote_stock"],
    #         "failure": ["file"]
    #     }

    #     # 2. 出力ディレクトリの作成
    #     daily_report_dir = os.path.join(self.test_output_dir, "daily", test_date, "reports")
    #     spot_report_dir = os.path.join(self.test_output_dir, "spot", test_date, "reports")
    #     os.makedirs(daily_report_dir, exist_ok=True)
    #     os.makedirs(spot_report_dir, exist_ok=True)

    #     # 3. テスト実行と検証
    #     with patch('app.core.config.get_request_config', return_value=self.test_config):
    #         # 日次実行レポート
    #         self.collector.create_execution_report('daily', test_date)
    #         self.assertTrue(
    #             os.path.exists(daily_report_dir), 
    #             f"ディレクトリが存在すること: {daily_report_dir}"
    #         )
    #         daily_reports = os.listdir(daily_report_dir)
    #         self.assertTrue(
    #             any(report.startswith("execution_report_") for report in daily_reports),
    #             "実行レポートファイルが作成されていること"
    #         )

    #         # スポット実行レポート
    #         self.collector.create_execution_report('spot', test_date)
    #         self.assertTrue(os.path.exists(spot_report_dir))
    #         spot_reports = os.listdir(spot_report_dir)
    #         self.assertTrue(
    #             any(report.startswith("execution_report_") for report in spot_reports),
    #             "実行レポートファイルが作成されていること"
    #         )