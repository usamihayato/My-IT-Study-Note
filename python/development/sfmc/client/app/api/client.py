import os
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import requests
from requests.exceptions import RequestException
from app.core.config import get_connection_config, get_output_path
from app.core.logger import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """APIレート制限の管理クラス"""
    
    def __init__(self, limits: Dict[str, int]):
        """
        レート制限管理の初期化
        
        Args:
            limits (Dict[str, int]): レート制限の設定
        """
        self.limits = limits
        self.requests = []
    
    def wait_if_needed(self) -> None:
        """必要に応じてレート制限による待機を行う"""
        now = datetime.now()
        
        # 古いリクエスト履歴を削除
        self.requests = [ts for ts in self.requests 
                        if now - ts < timedelta(minutes=1)]
        
        # 1分あたりの制限をチェック
        if len(self.requests) >= self.limits['per_minute']:
            sleep_time = 60 - (now - self.requests[0]).total_seconds()
            if sleep_time > 0:
                logger.info(f"レート制限により {sleep_time:.2f} 秒待機します")
                time.sleep(sleep_time)
        
        self.requests.append(now)


class SFMCClient:
    """SFMC API共通クライアント"""

    def __init__(self, mode: str, date: str):
        """
        クライアントの初期化

        Args:
            mode (str): 実行モード ('daily' or 'spot')
            date (str): 実行日付 (YYYYMMDD形式)
        """
        # 基本設定の読み込み
        self.config = get_connection_config()
        self.base_url = self.config['sfmc']['base_url'].rstrip('/')
        self.client_id = self.config['sfmc']['client_id']
        self.client_secret = self.config['sfmc']['client_secret']
        self.retry_config = self.config['retry']
        
        # 実行モードと出力設定
        self.mode = mode
        self.date = date
        self.output_dir = get_output_path(mode, date)
        
        # 認証関連
        self.access_token = None
        self.token_expiry = None
        
        # レート制限の初期化
        self.rate_limiter = RateLimiter(self.config['rate_limits']['rest_api'])
        self.msg_rate_limiter = RateLimiter(self.config['rate_limits']['transactional_messaging'])
        
        # 初期設定の実行
        self._init_proxy_settings()
        self._ensure_output_dir()
        
        logger.info(f"SFMCClientを初期化しました - mode: {mode}, date: {date}")

    # プライベートメソッド: 初期化関連
    def _init_proxy_settings(self) -> None:
        """プロキシ設定の初期化"""
        self.proxies = None
        if self.config.get('use_proxy', False) and self.config.get('proxies'):
            proxy = self.config['proxies']
            self.proxies = {
                'http': f"http://{proxy['host']}:{proxy['port']}",
                'https': f"https://{proxy['host']}:{proxy['port']}"
            }
            logger.info("プロキシ設定を適用しました")
        else:
            logger.info("プロキシは使用しません")

    def _ensure_output_dir(self) -> None:
        """出力ディレクトリの存在確認と作成"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            logger.info(f"出力ディレクトリを作成しました: {self.output_dir}")

    # プライベートメソッド: 認証関連
    def _get_auth_token(self) -> str:
        """認証トークンを取得または更新"""
        if self.access_token and self.token_expiry and datetime.now() < self.token_expiry - timedelta(seconds=self.config['sfmc']['auth']['token_refresh_margin_seconds']):
            return self.access_token

        auth_url = f"{self.base_url}{self.config['sfmc']['auth']['token_endpoint']}"
        payload = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }

        try:
            response = requests.post(
                auth_url,
                json=payload,
                proxies=self.proxies,
                timeout=self.config['sfmc']['connection']['timeout_seconds']
            )
            response.raise_for_status()
            token_data = response.json()
            
            self.access_token = token_data["access_token"]
            self.token_expiry = datetime.now() + timedelta(seconds=token_data["expires_in"])
            logger.debug("認証トークンを更新しました")
            
            return self.access_token
            
        except Exception as e:
            logger.error(f"認証トークンの取得に失敗しました: {str(e)}")
            raise

    def _get_headers(self) -> Dict[str, str]:
        """認証ヘッダーを生成"""
        return {
            "Authorization": f"Bearer {self._get_auth_token()}",
            "Content-Type": "application/json"
        }

    # プライベートメソッド: リクエスト実行関連
    def _make_request(
        self,
        method: str,
        url: str,
        is_transactional: bool = False,
        **kwargs
    ) -> requests.Response:
        """
        拡張されたAPIリクエスト実行メソッド

        Args:
            method (str): HTTPメソッド
            url (str): リクエストURL
            is_transactional (bool): トランザクショナルメッセージングAPIかどうか
            **kwargs: requestsライブラリに渡す追加のパラメータ

        Returns:
            requests.Response: APIレスポンス

        Raises:
            RequestException: APIリクエストでエラーが発生した場合
        """
        # レート制限の適用
        if is_transactional:
            self.msg_rate_limiter.wait_if_needed()
        else:
            self.rate_limiter.wait_if_needed()

        retry_wait = self.retry_config.get('initial_wait_seconds', 1.0)
        retry_limit = self.retry_config.get('max_attempts', 2)
        backoff_factor = self.retry_config.get('backoff_factor', 2)

        for retry_count in range(retry_limit + 1):
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    headers=self._get_headers(),
                    proxies=self.proxies,
                    **kwargs
                )
                
                # レスポンスコードのチェック
                if response.status_code in self.retry_config['status_forcelist']:
                    if retry_count >= retry_limit:
                        response.raise_for_status()
                    wait_time = retry_wait * (backoff_factor ** retry_count)
                    logger.warning(f"ステータスコード {response.status_code} のためリトライします。待機時間: {wait_time}秒")
                    time.sleep(wait_time)
                    continue
                    
                response.raise_for_status()
                return response

            except RequestException as e:
                logger.error(f"APIリクエストエラー: {str(e)}")
                
                # エラーの詳細をログに出力
                if hasattr(e.response, 'json'):
                    try:
                        error_detail = e.response.json()
                        logger.error(f"エラー詳細: {error_detail}")
                    except ValueError:
                        pass

                # 特定のエラーは即座に再スロー
                if e.response and e.response.status_code in self.retry_config['status_blacklist']:
                    raise

                if retry_count >= retry_limit:
                    raise

                wait_time = retry_wait * (backoff_factor ** retry_count)
                logger.info(f"リトライを実行します ({retry_count + 1}/{retry_limit}). 待機時間: {wait_time}秒")
                time.sleep(wait_time)

    def _save_response(
        self,
        response: requests.Response,
        prefix: str,
        include_request: bool = True
    ) -> str:
        """
        レスポンスをJSONファイルに保存
        
        Args:
            response (requests.Response): APIレスポンス
            prefix (str): ファイル名のプレフィックス
            include_request (bool): リクエスト情報も保存するかどうか
        
        Returns:
            str: 保存したファイルのパス
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(self.output_dir, f"{prefix}_{timestamp}.json")
        
        output_data = {
            "response": {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response.json() if response.content else None
            }
        }
        
        if include_request and response.request:
            output_data["request"] = {
                "method": response.request.method,
                "url": response.request.url,
                "headers": dict(response.request.headers),
                "body": response.request.body.decode('utf-8') if response.request.body else None
            }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"レスポンスを保存しました: {filepath}")
        return filepath