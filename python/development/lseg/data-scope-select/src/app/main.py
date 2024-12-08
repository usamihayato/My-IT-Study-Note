import time
import sys
import requests
from app.api.client import DataScopeClient
from app.core.config import get_data_config
from app.core.logger import setup_logging, get_logger
from app.core.logger import logger
from app.utils.file_handler import save_extracted_file

setup_logging()
logger = get_logger(__name__)

def main():
    client = DataScopeClient()
    data_config = get_data_config()

    try:
        # 認証してトークンを取得
        token = client.get_auth_token()
        logger.info(f"認証に成功しました。トークン: {token}")

        # 銘柄リストが存在するか確認し、なければ作成
        list_name = "my_instrument_list"
        list_id = client.get_instrument_list_id(list_name)
        if not list_id:
            list_id = client.create_instrument_list(list_name)
            logger.info(f"銘柄リストを作成しました: {list_name} (ID: {list_id})")
            instruments = data_config['instruments']
            client.append_instruments(list_id, instruments)
            logger.info(f"{len(instruments)}個の銘柄をリストに追加しました")
        else:
            logger.info(f"既存の銘柄リストを使用します: {list_name} (ID: {list_id})")
            # 新しい銘柄があるか確認し、あれば追加
            existing_instruments = client.get_instruments_in_list(list_id)
            new_instruments = [inst for inst in data_config['instruments'] if inst not in existing_instruments]
            if new_instruments:
                client.append_instruments(list_id, new_instruments)
                logger.info(f"{len(new_instruments)}個の新しい銘柄をリストに追加しました")
            else:
                logger.info("追加する新しい銘柄はありません")

        # レポートテンプレートが存在するか確認し、なければ作成
        template_name = "my_eod_template"
        template_id = client.get_report_template_id(template_name)
        if not template_id:
            content_fields = data_config['report_fields']
            template_id = client.create_report_template(template_name, content_fields)
            logger.info(f"レポートテンプレートを作成しました: {template_name} (ID: {template_id})")
        else:
            logger.info(f"既存のレポートテンプレートを使用します: {template_name} (ID: {template_id})")

        # スケジュールが存在するか確認し、なければ作成
        schedule_name = "my_eod_schedule"
        schedule_id = client.get_schedule_id(schedule_name)
        if not schedule_id:
            schedule_id = client.create_schedule(schedule_name, list_id, template_id, extraction_type='EOD')
            logger.info(f"スケジュールを作成しました: {schedule_name} (ID: {schedule_id})")
        else:
            logger.info(f"既存のスケジュールを使用します: {schedule_name} (ID: {schedule_id})")
            # スケジュールトリガーを現在の日付に更新
            client.update_schedule_trigger(schedule_id)
            logger.info(f"スケジュールトリガーを現在の日付に更新しました")

        # 抽出を実行し、結果をダウンロード
        status = client.get_extraction_status(schedule_id)
        while status['State'] != 'Completed':
            if status['State'] == 'Failed':
                logger.error(f"抽出に失敗しました。ステータス: {status}")
                break

            logger.info(f"抽出がまだ完了していません。ステータス: {status['State']}. 30秒待機します...")
            time.sleep(30)  # 30秒待機してから再度確認
            status = client.get_extraction_status(schedule_id)

        if status['State'] == 'Completed':
            # 抽出ファイルをダウンロードして保存
            file_id = status['Result']['FileId']
            output_path = data_config['output_path']
            client.download_extracted_file(file_id, output_path)
            logger.info(f"抽出ファイルをダウンロードして保存しました: {output_path}")

    except requests.exceptions.RequestException as e:
        logger.error(f"APIへのリクエスト中にエラーが発生しました: {str(e)}")
        sys.exit(1)

    except Exception as e:
        logger.error(f"予期しないエラーが発生しました: {str(e)}")
        sys.exit(1)

    finally:
        # クリーンアップ処理を実行
        pass


if __name__ == "__main__":
    main()