import unittest
from unittest.mock import patch, Mock, MagicMock
import os
import shutil
from app.api.client import QuickApiClient
from app.core.config import get_connection_config

class TestQuickApiClient(unittest.TestCase):
    """QuickApiClientのテスト"""

    def setUp(self):
        """テストの前準備"""
        # テスト用の出力ディレクトリ
        self.test_output_dir = os.path.join('output', 'test')
        os.makedirs(self.test_output_dir, exist_ok=True)

        # クライアントインスタンスの作成
        self.client = QuickApiClient(output_dir=self.test_output_dir)

    def tearDown(self):
        """テスト後のクリーンアップ"""
        # テスト用の出力ディレクトリのクリーンアップ
        if os.path.exists(self.test_output_dir):
            shutil.rmtree(self.test_output_dir)

    def test_init_client(self):
        """クライアントの初期化テスト"""
        config = get_connection_config()
        self.assertEqual(self.client.base_url, config['api']['base_url'])
        self.assertEqual(self.client.access_key, config['api']['access_key'])
        self.assertEqual(self.client.format, config['api']['format'])

    def test_validate_format_valid(self):
        """有効なレスポンス形式の検証テスト"""
        try:
            self.client._validate_format('csv')
            self.client._validate_format('json')
            self.client._validate_format('tsv')
        except ValueError:
            self.fail("有効なフォーマットで例外が発生しました")

    def test_validate_format_invalid(self):
        """無効なレスポンス形式の検証テスト"""
        with self.assertRaises(ValueError):
            self.client._validate_format('invalid_format')

    @patch('urllib.request.urlopen')
    def test_request_data_success(self, mock_urlopen):
        """データリクエスト成功のテスト"""
        # モックレスポンスの設定
        mock_response = Mock()
        mock_response.info.return_value = {'Content-Encoding': 'identity'}
        mock_response.read.return_value = b'test,data\n1,2\n'
        mock_response.headers = {}
        mock_urlopen.return_value.__enter__.return_value = mock_response

        output_path = os.path.join(self.test_output_dir, 'test_output.csv')
        filepath, universe_next = self.client.request_data(
            'quote_index',
            output_path,
            date='20231208'
        )

        self.assertTrue(os.path.exists(filepath))
        with open(filepath, 'r') as f:
            content = f.read()
            self.assertEqual(content, 'test,data\n1,2\n')