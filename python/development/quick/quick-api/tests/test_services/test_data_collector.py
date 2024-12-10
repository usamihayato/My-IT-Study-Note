import unittest
from unittest.mock import patch, Mock
import os
import shutil
import yaml
from datetime import datetime
from app.api.client import QuickApiClient
from app.services.data_collector import DataCollector
from app.core.config import get_connection_config

class TestDataCollector(unittest.TestCase):
    """DataCollectorのテスト"""

    @classmethod
    def setUpClass(cls):
        """テストクラス全体の前準備"""
        # 実際のconnection_configを読み込む
        cls.real_connection_config = get_connection_config()

    def setUp(self):
        """テストの前準備"""
        # テスト用の出力ディレクトリを作成
        self.test_output_dir = os.path.join('output', 'test')
        os.makedirs(os.path.join(self.test_output_dir, 'daily'), exist_ok=True)
        os.makedirs(os.path.join(self.test_output_dir, 'spot'), exist_ok=True)

        self.mock_client = Mock(spec=QuickApiClient)
        self.collector = DataCollector(self.mock_client)

        # テスト用の設定をセットアップ
        self.test_config = {
            'input': {
                'base_dir': 'input',
                'request_file': 'requests.yml',
                'daily_dir': 'daily',
                'spot_dir': 'spot'
            },
            'output': {
                'base_dir': 'output',
                'daily_dir': 'daily',
                'spot_dir': 'spot'
            }
        }

    def test_invalid_endpoint_name(self):
        """無効なエンドポイント名を含むリクエスト定義のテスト"""
        test_definition = {
            'requests': {
                'quote_inde': {  # 誤ったエンドポイント名
                    'enabled': True,
                    'description': "各種指標・直近データ"
                }
            }
        }

        with patch('app.core.config.get_request_config') as mock_get_config, \
             patch('yaml.safe_load') as mock_yaml_load, \
             patch('os.path.exists') as mock_exists:

            mock_get_config.return_value = self.test_config
            mock_yaml_load.return_value = test_definition
            mock_exists.return_value = True

            # エラーが発生することを確認
            with self.assertRaises(ValueError) as context:
                self.collector.validate_request_definition(test_definition)

            # エラーメッセージに具体的な情報が含まれていることを確認
            error_msg = str(context.exception)
            self.assertIn("quote_inde", error_msg)
            self.assertIn("無効なエンドポイント", error_msg)

    def test_invalid_endpoint_suggestion(self):
        """無効なエンドポイント名に対する提案機能のテスト"""
        test_definition = {
            'requests': {
                'quote_inde': {  # 誤ったエンドポイント名
                    'enabled': True,
                    'description': "各種指標・直近データ"
                }
            }
        }

        with patch('app.core.config.get_request_config') as mock_get_config, \
             patch('yaml.safe_load') as mock_yaml_load, \
             patch('os.path.exists') as mock_exists:

            mock_get_config.return_value = self.test_config
            mock_yaml_load.return_value = test_definition
            mock_exists.return_value = True

            # エラーが発生することを確認
            with self.assertRaises(ValueError) as context:
                self.collector.validate_request_definition(test_definition)

            # エラーメッセージに似ているエンドポイント名の提案が含まれていることを確認
            error_msg = str(context.exception)
            self.assertIn("quote_index", error_msg)  # 正しいエンドポイント名が提案されている

    def test_multiple_invalid_endpoints(self):
        """複数の無効なエンドポイントを含むリクエスト定義のテスト"""
        test_definition = {
            'requests': {
                'quote_inde': {  # 誤り1
                    'enabled': True,
                    'description': "各種指標・直近データ"
                },
                'foreign_fun': {  # 誤り2
                    'enabled': True,
                    'description': "外国投信・直近データ"
                }
            }
        }

        with patch('app.core.config.get_request_config') as mock_get_config, \
             patch('yaml.safe_load') as mock_yaml_load, \
             patch('os.path.exists') as mock_exists:

            mock_get_config.return_value = self.test_config
            mock_yaml_load.return_value = test_definition
            mock_exists.return_value = True

            # エラーが発生することを確認
            with self.assertRaises(ValueError) as context:
                self.collector.validate_request_definition(test_definition)

            # すべての無効なエンドポイントがエラーメッセージに含まれていることを確認
            error_msg = str(context.exception)
            self.assertIn("quote_inde", error_msg)
            self.assertIn("foreign_fun", error_msg)
            # 正しい名前の提案も含まれていることを確認
            self.assertIn("quote_index", error_msg)
            self.assertIn("foreign_fund", error_msg)

    def tearDown(self):
        """テスト後のクリーンアップ"""
        # テスト用の出力ディレクトリのクリーンアップ
        if os.path.exists(self.test_output_dir):
            shutil.rmtree(self.test_output_dir)

    def test_execute_spot_requests_file_not_found(self):
        """スポットリクエスト - ファイル未存在時のテスト"""
        test_date = "20240101"
        with patch('app.core.config.get_request_config') as mock_get_config:
            mock_get_config.return_value = self.test_config
            
            # 存在しない日付でのファイル未存在エラーを確認
            with self.assertRaises(FileNotFoundError) as context:
                self.collector.execute_spot_requests(test_date)
            
            self.assertIn("スポット定義ファイルが見つかりません", str(context.exception))

    def test_execute_spot_requests_with_existing_file(self):
        """スポットリクエスト - 定義ファイルが存在する場合のテスト"""
        # 実際のスポット定義ファイルを探す
        spot_dir = os.path.join('input', 'spot')
        if not os.path.exists(spot_dir):
            self.skipTest("スポット定義ディレクトリが存在しません")

        # 存在する日付ディレクトリを探す
        existing_dates = [d for d in os.listdir(spot_dir)
                         if os.path.isdir(os.path.join(spot_dir, d)) and
                         os.path.exists(os.path.join(spot_dir, d, 'requests.yml'))]

        if not existing_dates:
            self.skipTest("スポット定義ファイルが存在しません")

        # 利用可能な最新の日付を使用
        test_date = sorted(existing_dates)[-1]  # 最新の日付を使用
        spot_file_path = os.path.join(spot_dir, test_date, 'requests.yml')

        # 実際のリクエスト定義を読み込む
        with open(spot_file_path, 'r', encoding='utf-8') as f:
            actual_definition = yaml.safe_load(f)
            if not actual_definition or 'requests' not in actual_definition:
                self.skipTest("有効なリクエスト定義が存在しません")

        with patch('app.core.config.get_request_config') as mock_get_config:
            mock_get_config.return_value = self.test_config
            
            # モックの設定は最小限に
            self.mock_client.request_data.return_value = ('test_file.csv', None)
            
            # 実行
            results = self.collector.execute_spot_requests(test_date)
            
            # 実際のリクエスト定義に基づいて結果を検証
            enabled_requests = [req_name for req_name, req_def in actual_definition['requests'].items()
                              if req_def.get('enabled', True)]
            
            if enabled_requests:
                # 有効なリクエストが存在する場合
                self.assertTrue(
                    len(results['success']) > 0 or len(results['failure']) > 0,
                    "有効なリクエストが存在するのに実行結果がありません"
                )
            else:
                # 有効なリクエストが存在しない場合
                self.assertEqual(len(results['success']), 0)
                self.assertEqual(len(results['failure']), 0)