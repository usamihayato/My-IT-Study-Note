import sys
from datetime import datetime
from app.core.config import get_connection_config
from app.core.logger import setup_logging, get_logger
from app.api.client import SFMCClient

# ロガーの設定
setup_logging()
logger = get_logger('app.main')

def main():
    """認証APIのテスト実行"""
    try:
        # 実行時の設定
        mode = "daily"
        date = datetime.now().strftime('%Y%m%d')
        logger.info(f"処理を開始します - mode: {mode}, date: {date}")

        # クライアントの初期化
        logger.info("SFMCクライアントを初期化します")
        client = SFMCClient(mode=mode, date=date)
        
        # 認証トークンの取得テスト
        logger.info("認証トークンの取得を試みます")
        token = client._get_auth_token()
        logger.info("認証トークンの取得に成功しました")
        logger.info("処理を完了しました")

    except Exception as e:
        logger.error(f"エラーが発生しました: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()