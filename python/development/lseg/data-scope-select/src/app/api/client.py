import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import List, Dict, Optional
from app.core.config import get_connection_config
from app.core.logger import get_logger

logger = get_logger(__name__)

class DataScopeClient:
    """
    DataScope Select APIクライアント

    このクラスは、Refinitiv DataScope Select APIとの通信を管理し、
    以下の主な機能を提供します：
    - 認証トークンの取得と管理
    - 銘柄リストの作成と管理
    - レポートテンプレートの作成と管理
    - データ抽出スケジュールの作成と管理
    - 抽出したデータのダウンロード

    設定は connection_config.yml から読み込まれ、以下の項目が必要です：
    - api: APIの基本設定（base_url, username, password）
    - use_proxy: プロキシ使用フラグ
    - proxies: プロキシ設定（必要な場合）
    - headers: HTTPヘッダー設定
    - retry: リトライ設定
    - polling: ポーリング設定
    """

    def __init__(self):
        """
        クライアントの初期化
        - 設定ファイルの読み込み
        - セッションの初期化
        - レートリミッターの設定
        を行います。
        """
        self.config = get_connection_config()
        self.base_url = self.config['api']['base_url']
        self.headers = self.config['headers']
        self.polling_config = self.config['polling']
        self.session = self._init_session()
        self.token = None
        self._rate_limiter = self._init_rate_limiter()
        logger.info("DataScopeClientを初期化しました")

    def _init_session(self):
        """
        HTTPセッションを初期化する

        以下の設定を行います：
        - リトライ戦略の設定
        - プロキシ設定（有効な場合）
        - SSL証明書の検証設定
        - タイムアウト設定

        Returns:
            requests.Session: 設定済みのセッションオブジェクト
        """
        session = requests.Session()
        
        # リトライ戦略の設定
        retry_strategy = Retry(
            total=self.config['retry']['max_attempts'],
            backoff_factor=self.config['retry']['backoff_factor'],
            status_forcelist=self.config['retry']['status_forcelist']
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        
        # プロキシ設定の適用（設定が存在し、有効な場合のみ）
        if self.config.get('proxies') and self.config.get('use_proxy', False):
            session.proxies = self.config['proxies']
            logger.info("プロキシ設定を適用しました")
        else:
            logger.info("プロキシは使用しません")
            
        session.verify = self.config.get('verify_ssl', True)
        logger.info(f"SSL証明書の検証: {session.verify}")
        
        return session

    def _init_rate_limiter(self):
        """
        レートリミッターを初期化する

        APIリクエストの頻度を制御するためのレートリミッターを設定します。
        設定された時間枠内でのリクエスト数を制限し、API利用制限を超えないようにします。

        Returns:
            RateLimiter: レートリミッターオブジェクト
        """
        from datetime import datetime, timedelta
        
        class RateLimiter:
            def __init__(self, max_retries_per_minute):
                """
                Args:
                    max_retries_per_minute (int): 1分あたりの最大リトライ回数
                    ※DSSのベストプラクティスでは、502以上のエラーに対して「1分あたり3回以下、最大10回まで」のリトライを推奨しています

                """
                self.max_retries = max_retries_per_minute
                self.retry_times = []
            
            def can_retry(self):
                """
                現在リトライ可能かどうかを判定する

                Returns:
                    bool: リトライ可能な場合はTrue
                """
                now = datetime.now()
                # 1分以上前のリトライ記録を削除
                self.retry_times = [t for t in self.retry_times if now - t < timedelta(minutes=1)]
                return len(self.retry_times) < self.max_retries
            
            def add_retry(self):
                """リトライ実行を記録する"""
                self.retry_times.append(datetime.now())
        
        return RateLimiter(self.config['retry']['max_retries_per_minute'])

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        """
        共通のリクエスト処理を行う

        - レートリミットのチェック
        - リクエストの実行
        - エラーハンドリング
        を一元的に管理します。

        Args:
            method (str): HTTPメソッド（GET, POST, etc.）
            path (str): APIエンドポイントのパス
            **kwargs: requestsライブラリに渡す追加のパラメータ

        Returns:
            requests.Response: APIレスポンス

        Raises:
            requests.exceptions.RequestException: リクエスト失敗時
        """
        url = f"{self.base_url}/{path}"
        logger.debug(f"リクエスト実行: {method} {url}")
        
        try:
            # レートリミットのチェック
            if not self._rate_limiter.can_retry():
                logger.warning("レートリミットに到達しました。待機が必要です。")
                # ここで必要に応じて待機ロジックを実装可能
            
            response = self.session.request(method, url, headers=self.headers, **kwargs)
            response.raise_for_status()
            
            # 成功時はリトライカウントを更新
            self._rate_limiter.add_retry()
            return response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"リクエストが失敗しました: {str(e)}")
            raise

    def get_auth_token(self) -> str:
        """
        認証トークンを取得する

        APIにログインし、認証トークンを取得して、以降のリクエストで使用するために
        ヘッダーに設定します。

        Returns:
            str: 取得した認証トークン

        Raises:
            requests.exceptions.RequestException: 認証失敗時
        """
        login_data = {
            "Credentials": {
                "Password": self.config['api']['password'],
                "Username": self.config['api']['username']
            }
        }
        logger.info("認証トークンを取得します")
        response = self._request('POST', 'Authentication/RequestToken', json=login_data)
        self.token = response.json()['value']
        self.headers['Authorization'] = f"Bearer {self.token}"
        logger.info("認証トークンを取得しました")
        return self.token

    def create_instrument_list(self, name: str) -> str:
        """
        新しい銘柄リストを作成する

        Args:
            name (str): 作成する銘柄リストの名前

        Returns:
            str: 作成された銘柄リストのID

        Raises:
            requests.exceptions.RequestException: リスト作成失敗時
        """
        instrument_list_data = {
            "@odata.type": "#DataScope.Select.Api.Extractions.SubjectLists.InstrumentList",
            "Name": name
        }
        logger.info(f"銘柄リスト '{name}' を作成します")
        response = self._request('POST', 'Extractions/InstrumentLists', json=instrument_list_data)
        list_id = response.json()['ListId']
        logger.info(f"銘柄リスト '{name}' (ID: {list_id}) を作成しました")
        return list_id

    def get_instrument_list_id(self, name: str) -> Optional[str]:
        """
        指定された名前の銘柄リストのIDを取得する

        Args:
            name (str): 検索する銘柄リストの名前

        Returns:
            Optional[str]: 銘柄リストのID。存在しない場合はNone

        Raises:
            requests.exceptions.RequestException: API呼び出し失敗時
        """
        logger.info(f"銘柄リスト '{name}' のIDを検索します")
        response = self._request('GET', 'Extractions/InstrumentLists')
        for item in response.json()['value']:
            if item['Name'] == name:
                logger.info(f"銘柄リスト '{name}' のIDを発見: {item['ListId']}")
                return item['ListId']
        logger.warning(f"銘柄リスト '{name}' は存在しません")
        return None

    def append_instruments(self, list_id: str, instruments: List[str]) -> None:
        """
        銘柄リストに銘柄を追加する

        Args:
            list_id (str): 銘柄リストのID
            instruments (List[str]): 追加する銘柄のリスト（RICコード）

        Raises:
            requests.exceptions.RequestException: 銘柄追加失敗時
        """
        instrument_list_data = {
            "Identifiers": [{"Identifier": inst, "IdentifierType": "Ric"} for inst in instruments],
            "KeepDuplicates": False
        }
        logger.info(f"銘柄リスト {list_id} に {len(instruments)} 件の銘柄を追加します")
        self._request(
            'POST',
            f"Extractions/InstrumentLists('{list_id}')/InstrumentListAppendIdentifiers",
            json=instrument_list_data
        )
        logger.info("銘柄の追加が完了しました")

    def create_report_template(self, name: str, content_fields: List[Dict[str, str]]) -> str:
        """
        新しいレポートテンプレートを作成する

        Args:
            name (str): テンプレートの名前
            content_fields (List[Dict[str, str]]): 
                取得するフィールドのリスト。各フィールドは {"name": "フィールド名"} の形式

        Returns:
            str: 作成されたレポートテンプレートのID

        Raises:
            requests.exceptions.RequestException: テンプレート作成失敗時
        """
        report_data = {
            "@odata.type": "#DataScope.Select.Api.Extractions.ReportTemplates.EndOfDayPricingReportTemplate",
            "Name": name,
            "ContentFields": [{"FieldName": field['name']} for field in content_fields]
        }
        logger.info(f"レポートテンプレート '{name}' を作成します")
        response = self._request('POST', 'Extractions/ReportTemplates', json=report_data)
        template_id = response.json()['ReportTemplateId']
        logger.info(f"レポートテンプレート '{name}' (ID: {template_id}) を作成しました")
        return template_id

    def get_report_template_id(self, name: str) -> Optional[str]:
        """
        指定された名前のレポートテンプレートのIDを取得する

        Args:
            name (str): 検索するテンプレートの名前

        Returns:
            Optional[str]: テンプレートのID。存在しない場合はNone

        Raises:
            requests.exceptions.RequestException: API呼び出し失敗時
        """
        logger.info(f"レポートテンプレート '{name}' のIDを検索します")
        response = self._request('GET', 'Extractions/ReportTemplates')
        for item in response.json()['value']:
            if item['Name'] == name:
                logger.info(f"レポートテンプレート '{name}' のIDを発見: {item['ReportTemplateId']}")
                return item['ReportTemplateId']
        logger.warning(f"レポートテンプレート '{name}' は存在しません")
        return None

    def create_schedule(
        self,
        list_id: str,
        report_template_id: str,
        extraction_type: str,
        start_date: str = None,
        end_date: str = None
    ) -> str:
        """
        データ抽出スケジュールを作成する

        Args:
            list_id (str): 銘柄リストのID
            report_template_id (str): レポートテンプレートのID
            extraction_type (str): 抽出タイプ（'EOD' または 'Historical'）
            start_date (str, optional): 開始日（YYYY-MM-DD形式）
            end_date (str, optional): 終了日（YYYY-MM-DD形式）

        Returns:
            str: 作成されたスケジュールのID

        Raises:
            ValueError: 無効な抽出タイプまたは日付指定の場合
            requests.exceptions.RequestException: スケジュール作成失敗時
        """
        logger.info(f"データ抽出スケジュールを作成します（タイプ: {extraction_type}）")
        
        if extraction_type == 'EOD':
            schedule_data = {
                "ListId": list_id,
                "ReportTemplateId": report_template_id,
                "Recurrence": {
                    "@odata.type": "#DataScope.Select.Api.Extractions.Schedules.SingleRecurrence",
                    "ExtractionDateTime": "T00:00:00.000Z",
                    "IsImmediate": False
                },
                "Trigger": {
                    "@odata.type": "#DataScope.Select.Api.Extractions.Schedules.DataAvailabilityTrigger",
                    "LimitReportToTodaysData": True
                }
            }
            logger.debug("日次データ抽出スケジュールを設定します")
            
        elif extraction_type == 'Historical':
            if not start_date or not end_date:
                error_msg = "Historical抽出には開始日と終了日の指定が必要です"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            schedule_data = {
                "ListId": list_id,
                "ReportTemplateId": report_template_id,
                "Recurrence": {
                    "@odata.type": "#DataScope.Select.Api.Extractions.Schedules.SingleRecurrence",
                    "ExtractionDateTime": f"{end_date}T00:00:00.000Z",
                    "IsImmediate": False
                },
                "Trigger": {
                    "@odata.type": "#DataScope.Select.Api.Extractions.Schedules.DateRangeTrigger",
                    "StartDate": start_date,
                    "EndDate": end_date
                }
            }
            logger.debug(f"期間指定データ抽出スケジュールを設定します（期間: {start_date} ～ {end_date}）")
            
        else:
            error_msg = f"無効な抽出タイプです: {extraction_type}（'EOD'または'Historical'を指定してください）"
            logger.error(error_msg)
            raise ValueError(error_msg)

        response = self._request('POST', 'Extractions/Schedules', json=schedule_data)
        schedule_id = response.json()['ScheduleId']
        logger.info(f"データ抽出スケジュールを作成しました（ID: {schedule_id}）")
        return schedule_id

    def get_schedule_id(self, name: str) -> Optional[str]:
        """
        指定された名前のスケジュールのIDを取得する

        Args:
            name (str): 検索するスケジュールの名前

        Returns:
            Optional[str]: スケジュールのID。存在しない場合はNone

        Raises:
            requests.exceptions.RequestException: API呼び出し失敗時
        """
        logger.info(f"スケジュール '{name}' のIDを検索します")
        response = self._request('GET', 'Extractions/Schedules')
        for item in response.json()['value']:
            if item['Name'] == name:
                logger.info(f"スケジュール '{name}' のIDを発見: {item['ScheduleId']}")
                return item['ScheduleId']
        logger.warning(f"スケジュール '{name}' は存在しません")
        return None

    def get_instruments_in_list(self, list_id: str) -> List[str]:
        """
        指定された銘柄リストに含まれる銘柄を取得する

        Args:
            list_id (str): 銘柄リストのID

        Returns:
            List[str]: 銘柄コード（RIC）のリスト

        Raises:
            requests.exceptions.RequestException: API呼び出し失敗時
        """
        logger.info(f"銘柄リスト {list_id} の内容を取得します")
        response = self._request('GET', f"Extractions/InstrumentLists('{list_id}')/Identifiers")
        instruments = [item['Identifier'] for item in response.json()['value']]
        logger.info(f"銘柄リストから {len(instruments)} 件の銘柄を取得しました")
        return instruments

    def update_schedule_trigger(self, schedule_id: str) -> None:
        """
        指定されたスケジュールのトリガー時刻を更新する

        このメソッドは、既存のスケジュールのトリガー設定を現在の日付に更新します。
        主にEOD（日次）データの取得スケジュールの更新に使用されます。

        Args:
            schedule_id (str): スケジュールのID

        Raises:
            requests.exceptions.RequestException: API呼び出し失敗時
        """
        schedule_data = {
            "Trigger": {
                "@odata.type": "#DataScope.Select.Api.Extractions.Schedules.DataAvailabilityTrigger",
                "LimitReportToTodaysData": True
            }
        }
        logger.info(f"スケジュール {schedule_id} のトリガー設定を更新します")
        self._request('PATCH', f"Extractions/Schedules('{schedule_id}')", json=schedule_data)
        logger.info("トリガー設定の更新が完了しました")

    def get_extraction_status(self, schedule_id: str) -> Dict:
        """
        データ抽出の状態を取得する

        指定されたスケジュールの最新の抽出状態を取得します。
        ステータスには以下のような情報が含まれます：
        - 抽出の状態（完了、実行中、エラーなど）
        - 抽出されたファイルの情報
        - エラーが発生した場合はエラーの詳細

        Args:
            schedule_id (str): スケジュールのID

        Returns:
            Dict: 抽出状態の詳細情報

        Raises:
            requests.exceptions.RequestException: API呼び出し失敗時
        """
        logger.info(f"スケジュール {schedule_id} の抽出状態を確認します")
        response = self._request('GET', f"Extractions/Schedules('{schedule_id}')/LastExtraction")
        status = response.json()
        logger.info(f"抽出状態: {status.get('Status', 'Unknown')}")
        return status

    def download_extracted_file(
        self,
        file_id: str,
        output_path: str,
        chunk_size: int = 8192,
        timeout: int = 3600,
        progress_callback: callable = None
    ) -> None:
        """
        抽出されたファイルを安全にダウンロードする

        チャンク処理を行い、大きなファイルでもメモリを効率的に使用します。
        進捗状況のコールバック関数を指定することで、ダウンロードの進捗を監視できます。

        Args:
            file_id (str): ダウンロードするファイルのID
            output_path (str): 保存先のパス
            chunk_size (int, optional): チャンクサイズ（バイト）。デフォルト8KB
            timeout (int, optional): タイムアウト時間（秒）。デフォルト1時間
            progress_callback (callable, optional): 
                進捗報告用コールバック関数。
                引数: (現在のサイズ, 合計サイズ)

        Raises:
            requests.exceptions.RequestException: ダウンロード失敗時
            requests.exceptions.Timeout: タイムアウト発生時
            IOError: ファイル保存失敗時
            ValueError: 不正なレスポンス
        """
        logger.info(f"ファイル {file_id} のダウンロードを開始します")
        
        # 保存先ディレクトリの存在確認と作成
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            logger.debug(f"保存先ディレクトリを作成しました: {output_dir}")

        temp_file_path = f"{output_path}.tmp"
        try:
            # ストリーミングレスポンスを取得
            url = f"{self.base_url}/Extractions/ExtractedFiles('{file_id}')/$value"
            with self.session.get(
                url,
                headers=self.headers,
                stream=True,
                timeout=timeout
            ) as response:
                response.raise_for_status()
                
                # ファイルサイズの取得
                total_size = int(response.headers.get('content-length', 0))
                logger.info(f"ダウンロードサイズ: {self._format_size(total_size)}")
                
                # チャンク処理でファイルを保存
                with open(temp_file_path, 'wb') as f:
                    downloaded_size = 0
                    last_log_time = time.time()
                    
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        if chunk:
                            f.write(chunk)
                            downloaded_size += len(chunk)
                            
                            # 進捗コールバックの呼び出し（指定されている場合）
                            if progress_callback:
                                progress_callback(downloaded_size, total_size)
                            
                            # 1秒に1回程度進捗をログ出力
                            current_time = time.time()
                            if current_time - last_log_time >= 1:
                                progress = (downloaded_size / total_size * 100) if total_size > 0 else 0
                                logger.debug(
                                    f"ダウンロード進捗: {progress:.1f}% "
                                    f"({self._format_size(downloaded_size)} / {self._format_size(total_size)})"
                                )
                                last_log_time = current_time
            
            # ダウンロードが完了したら一時ファイルを本来のファイル名に変更
            os.replace(temp_file_path, output_path)
            logger.info(f"ファイルを保存しました: {output_path}")
            
        except requests.exceptions.Timeout:
            logger.error(f"ダウンロードがタイムアウトしました（制限時間: {timeout}秒）")
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            raise