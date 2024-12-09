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
    VALID_FORMATS = Literal["csv", "json", "tsv"]

    def __init__(self, output_dir: str = None, response_format: VALID_FORMATS = None):
        """
        クライアントの初期化

        Args:
            output_dir (str, optional): CSVファイルの保存先ディレクトリ
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
        if format_type not in ["csv", "json", "tsv"]:
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
        req.add_header("Accept-Encoding", "gzip")
        return req

    def _handle_response(self, response) -> Tuple[str, Optional[str]]:
        """レスポンスを処理する"""
        universe_next = response.headers.get('x-universe-next')
        if response.info().get("Content-Encoding") == "gzip":
            body = gzip.GzipFile(fileobj=response).read().decode("utf-8")
        else:
            body = response.read().decode("utf-8")
        return body, universe_next

    def _save_data(self, data: str, filename: str) -> str:
        """データをファイルに保存する"""
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(data)
        logger.info(f"ファイルを保存しました: {filepath}")
        return filepath

    def _request(
        self,
        endpoint_name: str,
        output_filename: str,
        params: Dict[str, str] = None,
        timeout: Optional[float] = None
    ) -> Tuple[str, Optional[str]]:
        """APIリクエストを実行し、結果をファイルに保存する"""
        endpoint = self.endpoints.get(endpoint_name)
        if not endpoint:
            raise ValueError(f"未定義のエンドポイント: {endpoint_name}")
            
        # URLの構築（フォーマット指定を含む）
        url = f"{self.base_url}/{endpoint['path']}.{self.format}"
        
        # クエリパラメータの追加
        if params:
            query_string = "&".join(f"{k}={v}" for k, v in params.items() if v is not None)
            url = f"{url}?{query_string}"

        logger.info(f"リクエストURL: {url}")
        
        retry_wait = self.retry_config.get('wait_seconds', 1.0)
        retry_limit = self.retry_config.get('max_attempts', 2)
        
        for retry_count in range(retry_limit + 1):
            try:
                request = self._create_request(url)
                if timeout:
                    response = urllib.request.urlopen(request, timeout=timeout)
                else:
                    response = urllib.request.urlopen(request)
                
                data, universe_next = self._handle_response(response)
                filepath = self._save_data(data, output_filename)
                return filepath, universe_next
                
            except HTTPError as he:
                logger.error(f"HTTPエラーが発生しました: {he}")
                if "x-description" in he.headers:
                    logger.error(f"エラー詳細: {he.headers['x-description']}")
                if 400 <= he.code < 500:
                    raise
                    
            except Exception as e:
                logger.error(f"エラーが発生しました: type={type(e)}, error={str(e)}")
                
            if retry_count >= retry_limit:
                logger.error(f"リトライ回数({retry_limit}回)を超過しました")
                raise
                
            logger.info(f"リトライを実行します ({retry_count + 1}/{retry_limit})")
            time.sleep(retry_wait)

    def request_data(
        self,
        endpoint_name: str,
        universe: Optional[str] = None,
        universe_next: Optional[str] = None,
        date: Optional[str] = None,
        filename: Optional[str] = None,
        format_type: Optional[VALID_FORMATS] = None
    ) -> Tuple[str, Optional[str]]:
        """データを取得してファイルに保存する"""
        endpoint = self.endpoints.get(endpoint_name)
        if not endpoint:
            raise ValueError(f"未定義のエンドポイント: {endpoint_name}")

        # フォーマットの一時的な変更
        original_format = self.format
        if format_type:
            self._validate_format(format_type)
            self.format = format_type

        try:
            # パラメータの構築
            params = {}
            if endpoint.get('use_universe') and universe:
                self._validate_universe(
                    endpoint_name.split('_')[0],
                    universe
                )
                params['universe'] = universe
                
            if endpoint.get('use_universe_next') and universe_next:
                params['universe_next'] = universe_next
                
            if date:
                params['date'] = date

            # ファイル名の生成
            if not filename:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"{endpoint_name}_{timestamp}.{self.format}"

            # リクエストの実行
            logger.info(
                f"{endpoint['description']}を取得します "
                f"[endpoint={endpoint_name}, format={self.format}]"
            )
            return self._request(
                endpoint_name,
                filename,
                params,
                timeout=self.config['api'].get('timeout')
            )
            
        finally:
            # フォーマットを元に戻す
            if format_type:
                self.format = original_format