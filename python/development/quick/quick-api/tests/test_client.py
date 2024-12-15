import unittest
from unittest.mock import patch, Mock, MagicMock
import os
import shutil
import csv
from datetime import datetime
from app.api.client import QuickApiClient
from app.core.config import get_connection_config, get_request_config

class TestQuickApiClient(unittest.TestCase):
    """QuickApiClientの拡張テスト"""

    @classmethod
    def setUpClass(cls):
        """テストクラス全体の前準備"""
        cls.connection_config = get_connection_config()
        cls.request_config = get_request_config()

    def setUp(self):
        """テストの前準備"""
        self.test_output_dir = os.path.join('output', 'test')
        os.makedirs(self.test_output_dir, exist_ok=True)
        self.client = QuickApiClient()

    def tearDown(self):
        """テスト後のクリーンアップ"""
        if os.path.exists(self.test_output_dir):
            shutil.rmtree(self.test_output_dir)

    def _validate_csv_headers(self, filepath: str, expected_headers: list):
        """CSVヘッダーの検証"""
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            headers = next(reader)
            self.assertEqual(set(headers), set(expected_headers), 
                           f"CSVヘッダーが期待値と異なります: {headers}")

    @patch('urllib.request.urlopen')
    def test_file_endpoint(self, mock_urlopen):
        """経済統計データ（file）エンドポイントのテスト"""
        # モックレスポンスの設定
        mock_response = Mock()
        mock_response.info.return_value = {'Content-Encoding': 'identity'}
        mock_response.headers = {}
        # 実際のレスポンス形式に基づくテストデータ
        mock_response.read.return_value = b'date,value\n20240410,100\n'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        # 最小日付でのリクエスト
        min_date = "20240410"
        output_path = os.path.join(self.test_output_dir, f'file_{min_date}.csv')
        filepath, _ = self.client.request_data('file', output_path, date=min_date)

        # ファイルの存在と内容を検証
        self.assertTrue(os.path.exists(filepath))
        self._validate_csv_headers(filepath, ['date', 'value'])

        # 日付なし（直近データ）のリクエスト
        output_path = os.path.join(self.test_output_dir, 'file_latest.csv')
        filepath, _ = self.client.request_data('file', output_path)
        self.assertTrue(os.path.exists(filepath))

        # 不正な日付でのリクエスト
        invalid_date = "20240409"
        with self.assertRaises(ValueError):
            self.client.request_data('file', output_path, date=invalid_date)

    @patch('urllib.request.urlopen')
    def test_foreign_fund_endpoint(self, mock_urlopen):
        """外国投信エンドポイントのテスト"""
        # 期待されるヘッダー（インターフェース仕様から）
        expected_headers = [
            'ifund_name', 'ifund_country', 'ifund_price', 'ifund_price_chg',
            'ifund_net_assets', 'ifund_net_assets_domestic', 'ifund_listed_date',
            'ifund_redemption_date', 'ifund_investment_adviser', 'ifund_return_m1m',
            'ifund_return_cum_m3m', 'ifund_return_cum_m6m', 'ifund_return_cum_m1y',
            'ifund_return_cum_m3y', 'ifund_return_cum_m5y', 'ifund_sd_annual_rate_m3y',
            'ifund_monthly_price', 'ifund_price_chg_m1m', 'ifund_monthly_date',
            'ifund_currency', 'ifund_quote_code'
        ]

        # ページング処理のテスト
        pages_data = [
            (b'ifund_name,ifund_country\nFund1,US\n', 'NEXT_1'),
            (b'ifund_name,ifund_country\nFund2,UK\n', None)
        ]

        for page_num, (data, universe_next) in enumerate(pages_data, 1):
            mock_response = Mock()
            mock_response.info.return_value = {'Content-Encoding': 'identity'}
            mock_response.headers = {'x-universe-next': universe_next} if universe_next else {}
            mock_response.read.return_value = data
            mock_urlopen.return_value.__enter__.return_value = mock_response

            output_path = os.path.join(self.test_output_dir, f'foreign_fund_p{page_num}.csv')
            filepath, next_token = self.client.request_data(
                'foreign_fund',
                output_path,
                universe_next='NEXT_1' if page_num > 1 else None
            )

            self.assertTrue(os.path.exists(filepath))
            self.assertEqual(next_token, universe_next)

    @patch('urllib.request.urlopen')
    def test_quote_foreign_stock_endpoint(self, mock_urlopen):
        """海外株エンドポイントのテスト"""
        # 期待されるヘッダー（インターフェース仕様から）
        expected_headers = [
            'short_name', 'data_date', 'price', 'price_time', 'calc_price',
            'calc_price_time', 'price_open', 'price_open_time', 'price_high',
            'price_high_time', 'price_low', 'price_low_time', 'price_chg',
            'price_pchg'
        ]

        # 各市場のテスト
        test_universes = ['usa_stock', 'lse_stock', 'hk_stock']
        
        for universe in test_universes:
            mock_response = Mock()
            mock_response.info.return_value = {'Content-Encoding': 'identity'}
            mock_response.headers = {}
            mock_response.read.return_value = b'short_name,data_date\nStock1,20231208\n'
            mock_urlopen.return_value.__enter__.return_value = mock_response

            output_path = os.path.join(self.test_output_dir, f'foreign_stock_{universe}.csv')
            filepath, _ = self.client.request_data(
                'quote_foreign_stock',
                output_path,
                universe=universe
            )

            self.assertTrue(os.path.exists(filepath))

        # 不正な市場コードでのテスト
        with self.assertRaises(ValueError):
            self.client.request_data(
                'quote_foreign_stock',
                'dummy.csv',
                universe='invalid_market'
            )

    @patch('urllib.request.urlopen')
    def test_quote_index_endpoint(self, mock_urlopen):
        """指標データエンドポイントのテスト"""
        # 期待されるヘッダー（インターフェース仕様から）
        expected_headers = [
            'short_name', 'data_date', 'price', 'price_time', 'calc_price',
            'calc_price_time', 'price_open', 'price_open_time', 'price_high',
            'price_high_time', 'price_low', 'price_low_time', 'price_chg',
            'price_pchg', 'ask_price', 'ask_price_time', 'bid_price',
            'bid_price_time', 'yield', 'yield_time', 'calc_yield',
            'calc_yield_time', 'yield_chg', 'cpd_yield', 'cpd_yield_time',
            'calc_cpd_yield', 'calc_cpd_yield_time', 'cpd_yield_chg'
        ]

        mock_response = Mock()
        mock_response.info.return_value = {'Content-Encoding': 'identity'}
        mock_response.headers = {}
        mock_response.read.return_value = b'short_name,data_date\nIndex1,20231208\n'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        output_path = os.path.join(self.test_output_dir, 'quote_index.csv')
        filepath, _ = self.client.request_data('quote_index', output_path)

        self.assertTrue(os.path.exists(filepath))
        self._validate_csv_headers(filepath, ['short_name', 'data_date'])

    def test_error_handling(self):
        """エラーハンドリングのテスト"""
        cases = [
            # API認証エラー
            {'status': 401, 'description': 'Unauthorized'},
            # レート制限エラー
            {'status': 429, 'description': 'Too Many Requests'},
            # サーバーエラー
            {'status': 500, 'description': 'Internal Server Error'},
        ]

        for case in cases:
            with self.subTest(case=case):
                with patch('urllib.request.urlopen') as mock_urlopen:
                    # エラーレスポンスの設定
                    mock_error = Mock()
                    mock_error.code = case['status']
                    mock_error.headers = {'x-description': case['description']}
                    mock_urlopen.side_effect = mock_error

                    output_path = os.path.join(self.test_output_dir, 'error_test.csv')
                    
                    # ステータスコードに応じた例外の発生を確認
                    with self.assertRaises(Exception) as context:
                        self.client.request_data('quote_index', output_path)