import argparse
from datetime import datetime
from app.api.client import QuickApiClient
from app.services.data_collector import DataCollector
from app.core.logger import setup_logging, get_logger


def main():
    setup_logging()
    logger = get_logger(__name__)

    parser = argparse.ArgumentParser(description='Quick APIデータ収集ツール')
    parser.add_argument(
        '--mode',
        choices=['daily', 'spot'],
        default='daily',
        help='実行モード（daily: 日次実行, spot: スポット実行）'
    )
    parser.add_argument(
        '--date',
        help='スポット実行時の定義日付（YYYYMMDD形式）'
    )

    args = parser.parse_args()

    try:
        client = QuickApiClient()
        collector = DataCollector(client)

        if args.mode == 'daily':
            logger.info("日次データ収集を開始します")
            results = collector.execute_daily_requests()
            collector.create_execution_report(mode='daily')
        else:
            if not args.date:
                raise ValueError("スポット実行には日付の指定が必要です（--date YYYYMMDD）")
            logger.info(f"スポットリクエスト（{args.date}）を実行します")
            results = collector.execute_spot_requests(args.date)
            collector.create_execution_report(mode='spot', date=args.date)

        # 結果のサマリーを表示
        success_count = len(results["success"])
        failure_count = len(results["failure"])
        logger.info(f"データ収集が完了しました（成功: {success_count}, 失敗: {failure_count}）")

    except Exception as e:
        logger.error(f"エラーが発生しました: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()