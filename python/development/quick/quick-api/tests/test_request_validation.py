import unittest
import os
import yaml
from datetime import datetime
from app.core.config import get_connection_config, get_request_config

class TestRequestValidation(unittest.TestCase):
    """リクエスト定義ファイルの妥当性検証テスト"""

    @classmethod
    def setUpClass(cls):
        """テストクラス全体の設定"""
        # 設定ファイルの読み込み
        cls.connection_config = get_connection_config()
        cls.request_config = get_request_config()
        
        # 有効なエンドポイント一覧を取得
        cls.valid_endpoints = set(cls.connection_config['endpoints'].keys())
        
        # 海外株式市場の有効なユニバース一覧を取得
        cls.valid_universes = set(cls.connection_config.get('universes', {}).get('foreign', {}).keys())

    def _load_yaml_file(self, filepath):
        """YAMLファイルを読み込む"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.fail(f"YAMLファイルの読み込みに失敗: {filepath}, エラー: {str(e)}")

    def _validate_file_endpoint(self, endpoint_config, mode):
        """fileエンドポイントの設定を検証"""
        # date形式のチェック
        if 'date' in endpoint_config:
            date_str = endpoint_config['date']
            try:
                date = datetime.strptime(date_str, '%Y%m%d')
                min_date = datetime.strptime(self.connection_config['endpoints']['file']['min_date'], '%Y%m%d')
                self.assertGreaterEqual(date, min_date, 
                    f"fileエンドポイントの日付が不正です: {date_str} < {min_date.strftime('%Y%m%d')}")
            except ValueError:
                self.fail(f"fileエンドポイントの日付形式が不正です: {date_str}")

        # date_rangeのチェック
        if 'date_range' in endpoint_config:
            self.assertIn('start_date', endpoint_config['date_range'], "date_rangeにstart_dateが必要です")
            self.assertIn('end_date', endpoint_config['date_range'], "date_rangeにend_dateが必要です")
            
            try:
                start_date = datetime.strptime(endpoint_config['date_range']['start_date'], '%Y%m%d')
                end_date = datetime.strptime(endpoint_config['date_range']['end_date'], '%Y%m%d')
                min_date = datetime.strptime(self.connection_config['endpoints']['file']['min_date'], '%Y%m%d')
                
                self.assertGreaterEqual(start_date, min_date,
                    f"start_dateが不正です: {start_date.strftime('%Y%m%d')} < {min_date.strftime('%Y%m%d')}")
                self.assertGreaterEqual(end_date, start_date,
                    "end_dateはstart_date以降である必要があります")
            except ValueError as e:
                self.fail(f"date_rangeの日付形式が不正です: {str(e)}")

    def _validate_quote_foreign_stock_endpoint(self, endpoint_config):
        """quote_foreign_stockエンドポイントの設定を検証"""
        self.assertIn('markets', endpoint_config, 
            "quote_foreign_stockには'markets'の指定が必要です")
        
        markets = endpoint_config['markets']
        self.assertTrue(isinstance(markets, list), 
            "marketsはリスト形式で指定する必要があります")
        
        for market in markets:
            self.assertIn(market, self.valid_universes,
                f"無効な市場コードが指定されています: {market}")

    def _validate_request_definition(self, definition, mode):
        """リクエスト定義の内容を検証"""
        self.assertIn('requests', definition, "requestsセクションが必要です")
        
        # スポット実行の場合はmetadataを確認
        if mode == 'spot':
            self.assertIn('metadata', definition, "スポット実行にはmetadataセクションが必要です")
            metadata = definition['metadata']
            self.assertIn('description', metadata, "metadataにdescriptionが必要です")
            self.assertIn('created_by', metadata, "metadataにcreated_byが必要です")
            self.assertIn('created_at', metadata, "metadataにcreated_atが必要です")

        # 各エンドポイントの設定を検証
        for endpoint_name, endpoint_config in definition['requests'].items():
            # エンドポイント名の検証
            self.assertIn(endpoint_name, self.valid_endpoints,
                f"未定義のエンドポイント: {endpoint_name}")
            
            # 必須項目の検証
            self.assertIn('description', endpoint_config,
                f"エンドポイント {endpoint_name} にdescriptionが必要です")

            # エンドポイント固有の検証
            if endpoint_name == 'file':
                self._validate_file_endpoint(endpoint_config, mode)
            elif endpoint_name == 'quote_foreign_stock':
                self._validate_quote_foreign_stock_endpoint(endpoint_config)

    def test_daily_request_definition(self):
        """日次実行用request.ymlの検証"""
        daily_path = os.path.join(
            self.request_config['input']['base_dir'],
            self.request_config['input']['daily_dir'],
            self.request_config['input']['request_file']
        )
        
        if not os.path.exists(daily_path):
            self.skipTest(f"日次実行定義ファイルが存在しません: {daily_path}")
            
        definition = self._load_yaml_file(daily_path)
        self._validate_request_definition(definition, 'daily')

    def test_spot_request_definitions(self):
        """スポット実行用request.ymlの検証"""
        spot_dir = os.path.join(
            self.request_config['input']['base_dir'],
            self.request_config['input']['spot_dir']
        )
        
        if not os.path.exists(spot_dir):
            self.skipTest(f"スポット実行ディレクトリが存在しません: {spot_dir}")

        # すべての日付ディレクトリをチェック
        for date_dir in os.listdir(spot_dir):
            if not os.path.isdir(os.path.join(spot_dir, date_dir)):
                continue
                
            spot_path = os.path.join(
                spot_dir,
                date_dir,
                self.request_config['input']['request_file']
            )
            
            if not os.path.exists(spot_path):
                continue
                
            with self.subTest(date=date_dir):
                definition = self._load_yaml_file(spot_path)
                self._validate_request_definition(definition, 'spot')