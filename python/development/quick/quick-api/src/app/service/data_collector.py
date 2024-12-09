import os
import yaml
import time
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
from app.api.client import QuickApiClient
from app.core.logger import get_logger

logger = get_logger(__name__)

class DataCollector:
    """データ収集サービス"""

    def __init__(self, client: QuickApiClient):
        self.client = client
        self.results = {
            "success": [],
            "failure": []
        }

    def _load_request_definition(self, filepath: str) -> dict:
        """リクエスト定義ファイルを読み込む"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"定義ファイルの読み込みに失敗しました: {filepath}, エラー: {e}")
            raise

    def execute_daily_requests(self) -> Dict[str, List[str]]:
        """日次データ収集を実行"""
        logger.info("日次データ収集を開始します")
        
        # 日次定義ファイルの読み込み
        daily_def_path = "input/daily/requests.yml"
        if not os.path.exists(daily_def_path):
            raise FileNotFoundError(f"日次定義ファイルが見つかりません: {daily_def_path}")
            
        definition = self._load_request_definition(daily_def_path)
        requests = definition.get('requests', {})
        
        # 各リクエストの実行
        for name, config in requests.items():
            if not config.get('enabled', False):
                logger.info(f"スキップ: {name} (無効化されています)")
                continue

            logger.info(f"{config['description']}を開始します")
            try:
                if name == 'foreign_stock':
                    self._collect_foreign_stock_data(config)
                else:
                    self._collect_simple_data(name, config)
            except Exception as e:
                logger.error(f"{name}の取得に失敗しました: {e}")
                self.results["failure"].append(name)

        return self.results

    def execute_spot_requests(self, date: str) -> Dict[str, List[str]]:
        """指定日のスポットリクエストを実行"""
        logger.info(f"スポットリクエスト（{date}）を開始します")
        
        # スポット定義ファイルの読み込み
        spot_def_path = f"input/spot/{date}/requests.yml"
        if not os.path.exists(spot_def_path):
            raise FileNotFoundError(f"スポット定義ファイルが見つかりません: {spot_def_path}")
            
        definition = self._load_request_definition(spot_def_path)
        metadata = definition.get('metadata', {})
        requests = definition.get('requests', {})
        
        logger.info(f"定義情報: {metadata.get('description', '説明なし')}")
        
        # 出力ディレクトリの準備
        output_base = f"output/spot/{date}"
        os.makedirs(output_base, exist_ok=True)
        
        # 各リクエストの実行
        for name, config in requests.items():
            logger.info(f"{config['description']}を開始します")
            try:
                request_type = config.get('type')
                if request_type == 'date_range':
                    self._collect_historical_data(name, config, output_base)
                elif request_type == 'all':
                    self._collect_all_data(name, config, output_base)
                else:
                    raise ValueError(f"未対応のリクエストタイプ: {request_type}")
                    
                self.results["success"].append(name)
            except Exception as e:
                logger.error(f"{name}の実行に失敗しました: {e}")
                self.results["failure"].append(name)

        return self.results

    def _collect_foreign_stock_data(self, config: dict):
        """海外株データの収集"""
        for market in config.get('markets', []):
            try:
                self._handle_retry(
                    self.client.get_foreign_stock,
                    retry_config=config.get('retry'),
                    universe=market
                )
                self.results["success"].append(f"foreign_stock_{market}")
            except Exception as e:
                logger.error(f"海外株データの取得に失敗: {market}, エラー: {e}")
                self.results["failure"].append(f"foreign_stock_{market}")

    def _collect_historical_data(self, name: str, config: dict, output_base: str):
        """期間指定の履歴データ収集"""
        params = config.get('parameters', {})
        output_file = f"{output_base}/{name}.csv"
        
        self._handle_retry(
            self.client.request_data,
            retry_config=config.get('retry'),
            endpoint_name=name,
            date_from=params.get('start_date'),
            date_to=params.get('end_date'),
            filename=output_file
        )

    def _collect_all_data(self, name: str, config: dict, output_base: str):
        """全量データ収集"""
        universe_next = None
        file_index = 1
        
        while True:
            output_file = f"{output_base}/{name}_{file_index}.csv"
            
            filepath, universe_next = self._handle_retry(
                self.client.request_data,
                retry_config=config.get('retry'),
                endpoint_name=name,
                universe_next=universe_next,
                filename=output_file
            )
            
            if not universe_next:
                break
                
            file_index += 1
            time.sleep(config.get('retry', {}).get('interval', 60))

    def _handle_retry(self, func, retry_config: dict = None, **kwargs):
        """リトライ処理を実行"""
        max_attempts = retry_config.get('max_attempts', 3) if retry_config else 3
        interval = retry_config.get('interval', 60) if retry_config else 60

        for attempt in range(max_attempts):
            try:
                return func(**kwargs)
            except Exception as e:
                if attempt + 1 == max_attempts:
                    raise
                logger.warning(f"エラーが発生しました（リトライ {attempt + 1}/{max_attempts}）: {e}")
                time.sleep(interval)

    def create_execution_report(self, mode: str, date: str = None):
        """実行結果レポートを作成"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 実行モードに応じてディレクトリを決定
        if mode == 'daily':
            report_dir = "output/daily/reports"
        else:
            report_dir = f"output/spot/{date}/reports"
            
        os.makedirs(report_dir, exist_ok=True)
        
        report_path = os.path.join(report_dir, f"execution_report_{timestamp}.txt")
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"実行結果レポート - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"実行モード: {mode}\n")
            if date:
                f.write(f"対象日付: {date}\n")
            f.write("=" * 50 + "\n\n")
            
            f.write("成功:\n")
            for item in self.results["success"]:
                f.write(f"  - {item}\n")
            
            f.write("\n失敗:\n")
            for item in self.results["failure"]:
                f.write(f"  - {item}\n")