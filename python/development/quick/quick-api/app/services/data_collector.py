import os
import yaml
import time
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
from app.api.client import QuickApiClient
from app.core.config import get_input_path, get_output_path, get_request_config
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
        
        execution_date = datetime.now().strftime("%Y%m%d")
        daily_def_path = get_input_path('daily')
        if not os.path.exists(daily_def_path):
            raise FileNotFoundError(f"日次定義ファイルが見つかりません: {daily_def_path}")
            
        definition = self._load_request_definition(daily_def_path)
        requests = definition.get('requests', {})
        
        # 出力ディレクトリを daily/YYYYMMDD/data 配下に設定
        base_dir = get_output_path('daily', execution_date)
        
        for name, config in requests.items():
            if not config.get('enabled', True):
                logger.info(f"スキップ: {name} (無効化されています)")
                continue

            logger.info(f"{config['description']}を開始します")
            try:
                self._execute_request(name, config, base_dir)
            except Exception as e:
                logger.error(f"{name}の取得に失敗しました: {e}")
                self.results["failure"].append(name)
            else:
                self.results["success"].append(name)

        return self.results

    def execute_spot_requests(self, target_date: str) -> Dict[str, List[str]]:
        """スポットリクエストを実行"""
        logger.info(f"スポットリクエスト（{target_date}）を開始します")
        
        spot_def_path = get_input_path('spot', target_date)
        if not os.path.exists(spot_def_path):
            raise FileNotFoundError(f"スポット定義ファイルが見つかりません: {spot_def_path}")
            
        definition = self._load_request_definition(spot_def_path)
        requests = definition.get('requests', {})
        
        # 出力ディレクトリを spot/YYYYMMDD/data 配下に設定
        base_dir = get_output_path('spot', target_date)
        
        for name, config in requests.items():
            logger.info(f"{config['description']}を開始します")
            try:
                self._execute_request(name, config, base_dir)
            except Exception as e:
                logger.error(f"{name}の取得に失敗しました: {e}")
                self.results["failure"].append(name)
            else:
                self.results["success"].append(name)

        return self.results

    def _execute_request(self, name: str, config: dict, base_dir: str):
        """個別リクエストを実行"""
        try:
            if 'date_range' in config:
                # 期間指定のリクエスト
                date_range = config['date_range']                
                # universe_next対応の処理追加
                universe_next = None
                page = 1
                
                while True:
                    # ページ番号付きのファイル名を生成
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_filename = f"{name}_{timestamp}"
                    if page > 1:
                        output_filename += f"_page{page}"
                    output_filename += ".csv"
                    output_path = os.path.join(base_dir, output_filename)

                    # データ取得
                    filepath, universe_next = self.client.request_data(
                        endpoint=name,
                        output_path=output_path,
                        date_from=date_range.get('start_date'),
                        date_to=date_range.get('end_date'),
                        universe_next=universe_next
                    )

                    # 続きのデータがない場合は終了
                    if not universe_next:
                        break

                    page += 1
                    time.sleep(1)  # APIレート制限を考慮

            else:
                # 通常のリクエスト
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                # universe_next対応の処理追加
                universe_next = None
                page = 1
                
                while True:
                    output_filename = f"{name}_{timestamp}"
                    if page > 1:
                        output_filename += f"_page{page}"
                    output_filename += ".csv"
                    output_path = os.path.join(base_dir, output_filename)

                    filepath, universe_next = self.client.request_data(
                        endpoint=name,
                        output_path=output_path,
                        universe_next=universe_next
                    )

                    if not universe_next:
                        break

                    page += 1
                    time.sleep(1)

            # リクエスト全体の成功を1回だけ記録
            if name not in self.results["success"]:
                self.results["success"].append(name)
                
        except Exception as e:
            logger.error(f"{name}の実行中にエラーが発生しました: {e}")
            if name not in self.results["failure"]:
                self.results["failure"].append(name)
            raise

    def create_execution_report(self, mode: str, date: Optional[str] = None):
        """実行結果レポートを作成"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        execution_date = date or datetime.now().strftime("%Y%m%d")
        
        config = get_request_config()
        base_output = config['output']['base_dir']
        
        if mode == 'daily':
            report_dir = os.path.join(base_output, config['output']['daily_dir'], execution_date, "reports")
        else:  # spot
            report_dir = os.path.join(base_output, config['output']['spot_dir'], execution_date, "reports")
            
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
