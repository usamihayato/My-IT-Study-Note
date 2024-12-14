import os
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import requests
from requests.exceptions import RequestException
from app.core.config import get_connection_config, get_output_path
from app.core.logger import get_logger

logger = get_logger(__name__)

class SFMCClient:
    """SFMC API クライアント"""

    def __init__(self, mode: str, date: str):
        """
        クライアントの初期化

        Args:
            mode (str): 実行モード ('daily' or 'spot')
            date (str): 実行日付 (YYYYMMDD形式)
        """
        self.config = get_connection_config()
        self.base_url = self.config['sfmc']['base_url'].rstrip('/')
        self.client_id = self.config['sfmc']['client_id']
        self.client_secret = self.config['sfmc']['client_secret']
        self.retry_config = self.config['retry']
        self.mode = mode
        self.date = date
        self.output_dir = get_output_path(mode, date)
        self.access_token = None
        self.token_expiry = None

        self._init_proxy_settings()
        self._ensure_output_dir()
        logger.info(f"SFMCClientを初期化しました - mode: {mode}, date: {date}")

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

    def _get_auth_token(self) -> str:
        """認証トークンを取得または更新"""
        if self.access_token and self.token_expiry and datetime.now() < self.token_expiry:
            return self.access_token

        auth_url = f"{self.base_url}/v2/token"
        payload = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }

        try:
            response = requests.post(auth_url, json=payload)
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

    def _make_request(
        self,
        method: str,
        url: str,
        json: Dict = None,
        params: Dict = None
    ) -> requests.Response:
        """APIリクエストを実行する"""
        retry_wait = self.retry_config.get('wait_seconds', 1.0)
        retry_limit = self.retry_config.get('max_attempts', 2)

        for retry_count in range(retry_limit + 1):
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    headers=self._get_headers(),
                    json=json,
                    params=params,
                    proxies=self.proxies
                )
                response.raise_for_status()
                return response

            except RequestException as e:
                logger.error(f"APIリクエストエラー: {str(e)}")
                if hasattr(e.response, 'json'):
                    try:
                        error_detail = e.response.json()
                        logger.error(f"エラー詳細: {error_detail}")
                    except ValueError:
                        pass

                if 400 <= e.response.status_code < 500:
                    raise
                if retry_count >= retry_limit:
                    raise

                logger.info(f"リトライを実行します ({retry_count + 1}/{retry_limit})")
                time.sleep(retry_wait)

    def _save_response(self, response: requests.Response, prefix: str) -> str:
        """レスポンスをファイルに保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(self.output_dir, f"{prefix}_{timestamp}.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(response.text)
        logger.info(f"レスポンスを保存しました: {filepath}")
        return filepath

    def upsert_data_extension_rows(
        self,
        external_key: str,
        rows: List[Dict],
        save_response: bool = True
    ) -> Dict[str, Any]:
        """
        データエクステンションにデータをアップサート
        Args:
            external_key (str): データエクステンションの外部キー
            rows (List[Dict]): アップサートするデータの配列
            save_response (bool, optional): レスポンスを保存するかどうか
        Returns:
            Dict[str, Any]: APIレスポンス
        """
        endpoint = f"{self.base_url}/hub/v1/dataevents/key:{external_key}/rowset"
        
        formatted_rows = [{
            "keys": {key: value for key, value in row.items() if key in row.get("keys", [])},
            "values": {key: value for key, value in row.items() if key not in row.get("keys", [])}
        } for row in rows]

        response = self._make_request('POST', endpoint, json=formatted_rows)
        result = response.json()

        if save_response:
            self._save_response(response, "de_upsert")

        return result

    def trigger_email_send(
        self,
        definition_key: str,
        recipient: Dict[str, str],
        attributes: Optional[Dict] = None,
        save_response: bool = True
    ) -> Dict[str, Any]:
        """
        トリガーメールを送信
        Args:
            definition_key (str): メール定義の外部キー
            recipient (Dict[str, str]): 送信先情報
            attributes (Optional[Dict]): カスタム属性
            save_response (bool, optional): レスポンスを保存するかどうか
        Returns:
            Dict[str, Any]: APIレスポンス
        """
        endpoint = f"{self.base_url}/messaging/v1/messageDefinitionSends/key:{definition_key}/send"
        
        payload = {
            "To": {
                "Address": recipient.get("email"),
                "SubscriberKey": recipient.get("subscriber_key", recipient.get("email")),
                "ContactAttributes": {
                    "SubscriberAttributes": attributes or {}
                }
            }
        }

        response = self._make_request('POST', endpoint, json=payload)
        result = response.json()

        if save_response:
            self._save_response(response, "email_send")

        return result

    def create_contact(
        self,
        contact_data: Dict,
        save_response: bool = True
    ) -> Dict[str, Any]:
        """
        連絡先を作成または更新
        Args:
            contact_data (Dict): 連絡先データ
            save_response (bool, optional): レスポンスを保存するかどうか
        Returns:
            Dict[str, Any]: APIレスポンス
        """
        endpoint = f"{self.base_url}/contacts/v1/contacts"
        
        payload = {
            "contactKey": contact_data.get("email"),
            "attributeSets": [{
                "name": "Email Addresses",
                "items": [{
                    "values": [{
                        "name": "Email Address",
                        "value": contact_data.get("email")
                    }]
                }]
            }],
            "attributes": [
                {"name": key, "value": value}
                for key, value in contact_data.items()
                if key != "email"
            ]
        }

        response = self._make_request('POST', endpoint, json=payload)
        result = response.json()

        if save_response:
            self._save_response(response, "contact_create")

        return result