import os
import gzip
import time
from typing import Dict, Optional, Tuple, Literal
from urllib.error import HTTPError
import urllib.request
from app.core.config import get_connection_config
from app.core.logger import get_logger

logger = get_logger(__name__)

class QuickApiClient:
    """Quick API クライアント"""

    # 有効なレスポンス形式
    ResponseFormat = Literal["csv", "json", "tsv"]
    VALID_FORMATS = ["csv", "json", "tsv"]

    def __init__(self, output_dir: str = None, response_format: VALID_FORMATS = None):
        """
        クライアントの初期化

        Args:
            output_dir (str, optional): ファイルの保存先ディレクトリ
            response_format (str, optional): レスポンス形式（"csv", "json", "tsv"）
        """
        self.config = get_connection_config()
        self.base_url = self.config['api']['base_url'].rstrip('/')
        self.access_key = self.config['api']['access_key']
        self.retry_config = self.config['retry']
        self.output_dir = output_dir or self.config.get('output_dir', 'output/data')
        self.endpoints = self.config['endpoints']
        self.universes = self.config.get('universes', {})
        self.format = response_format or self.config['api'].get('format', 'csv')
        
        self._validate_format(self.format)
        self._init_proxy_settings()
        self._ensure_output_dir()
        logger.info(f"QuickApiClientを初期化しました（レスポンス形式: {self.format}）")

    def _validate_format(self, format_type: str) -> None:
        """レスポンス形式の検証"""
        if format_type not in self.VALID_FORMATS:
            raise ValueError(f"無効なレスポンス形式です: {format_type}")

    def _init_proxy_settings(self) -> None:
        """プロキシ設定の初期化"""
        self.proxy_settings = {}
        if self.config.get('use_proxy', False) and self.config.get('proxies'):
            proxy = self.config['proxies']
            self.proxy_settings = {
                'proxyHost': proxy.get('host'),
                'proxyPort': str(proxy.get('port'))
            }
            logger.info("プロキシ設定を適用しました")
        else:
            logger.info("プロキシは使用しません")

    def _ensure_output_dir(self) -> None:
        """出力ディレクトリの存在確認と作成"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            logger.info(f"出力ディレクトリを作成しました: {self.output_dir}")

    def _create_request(self, url: str) -> urllib.request.Request:
        """リクエストオブジェクトを作成"""
        logger.debug(f"リクエストURL: {url}")
        req = urllib.request.Request(url)
        if self.proxy_settings:
            req.set_proxy(
                f"{self.proxy_settings['proxyHost']}:{self.proxy_settings['proxyPort']}",
                "http"
            )
        req.add_header("Authorization", f"Bearer {self.access_key}")
        return req

    def _handle_response(self, response) -> Tuple[str, Optional[str]]:
        """レスポンスを処理する"""
        universe_next = response.headers.get('x-universe-next')
        if response.info().get("Content-Encoding") == "gzip":
            body = gzip.GzipFile(fileobj=response).read().decode("utf-8")
        else:
            body = response.read().decode("utf-8")
        return body, universe_next

    def _save_data(self, data: str, filepath: str) -> str:
        """データをファイルに保存する"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(data)
        logger.info(f"ファイルを保存しました: {filepath}")
        return filepath

    def _request(
        self,
        endpoint: str,
        output_path: str,
        params: Dict[str, str] = None,
        format_type: Optional[str] = None
    ) -> Tuple[str, Optional[str]]:
        """APIリクエストを実行する"""
        # エンドポイントの存在確認
        if endpoint not in self.endpoints:
            raise ValueError(f"未定義のエンドポイント: {endpoint}")

        # フォーマット指定の処理
        current_format = format_type or self.format
        self._validate_format(current_format)

        # URLの構築
        url = f"{self.base_url}/{self.endpoints[endpoint]['path']}.{current_format}"
        if params:
            query_string = "&".join(f"{k}={v}" for k, v in params.items() if v is not None)
            url = f"{url}?{query_string}"

        retry_wait = self.retry_config.get('wait_seconds', 1.0)
        retry_limit = self.retry_config.get('max_attempts', 2)

        for retry_count in range(retry_limit + 1):
            try:
                request = self._create_request(url)
                with urllib.request.urlopen(request) as response:
                    data, universe_next = self._handle_response(response)
                    filepath = self._save_data(data, output_path)
                    return filepath, universe_next

            except HTTPError as he:
                logger.error(f"HTTPエラーが発生しました: {he}")
                if "x-description" in he.headers:
                    logger.error(f"エラー詳細: {he.headers['x-description']}")
                if 400 <= he.code < 500:
                    raise
                if retry_count >= retry_limit:
                    raise

            except Exception as e:
                logger.error(f"エラーが発生しました: {str(e)}")
                if retry_count >= retry_limit:
                    raise

            logger.info(f"リトライを実行します ({retry_count + 1}/{retry_limit})")
            time.sleep(retry_wait)

    def request_data(
        self,
        endpoint: str,
        output_path: str,
        date: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        universe: Optional[str] = None,
        universe_next: Optional[str] = None,
        format_type: Optional[str] = None
    ) -> Tuple[str, Optional[str]]:
        """
        データを取得してファイルに保存する
        Args:
            endpoint (str): エンドポイント名
            output_path (str): 出力ファイルパス
            date (Optional[str]): 取得日（YYYYMMDD形式）
            date_from (Optional[str]): 開始日（YYYYMMDD形式）
            date_to (Optional[str]): 終了日（YYYYMMDD形式）
            universe (Optional[str]): ユニバース指定
            universe_next (Optional[str]): 続きのデータ取得用識別子
            format_type (Optional[str]): レスポンス形式の一時的な指定
        Returns:
            Tuple[str, Optional[str]]: (保存したファイルパス, 次のuniverse_next)
        """
        params = {}
        if date:
            params['date'] = date
        if date_from:
            params['date_from'] = date_from
        if date_to:
            params['date_to'] = date_to
        if universe:
            params['universe'] = universe
        if universe_next:
            params['universe_next'] = universe_next

        return self._request(endpoint, output_path, params, format_type)