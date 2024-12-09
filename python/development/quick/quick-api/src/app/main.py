import os
from datetime import datetime
import logging.config
import yaml
from app.core.logger import setup_logging, get_logger
from app.api.client import QuickApiClient

def main():
    # ログ設定の読み込み
    setup_logging()
    logger = get_logger(__name__)

    try:
        # クライアントの初期化
        client = QuickApiClient(output_dir="output/data")
        logger.info("QuickApiClientの初期化が完了しました")
        
        # quote_indexデータの取得
        filepath, _ = client.request_data('quote_index')
        logger.info(f"データを保存しました: {filepath}")

    except Exception as e:
        logger.error(f"エラーが発生しました: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()