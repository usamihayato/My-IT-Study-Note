import time
from app.api.client import DataScopeClient
from app.core.config import get_data_config
from app.core.logger import logger
from app.utils.file_handler import save_extracted_file

def main():
    client = DataScopeClient()
    data_config = get_data_config()

    try:
        # Authenticate and get token
        token = client.get_auth_token()
        logger.info(f"認証に成功しました。トークン: {token}")

        # Create instrument list
        list_name = "my_instrument_list"
        list_id = client.create_instrument_list(list_name)
        logger.info(f"instrument listを作成しました: {list_name} (ID: {list_id})")

        # Append instruments to the list
        instruments = data_config['instruments']
        client.append_instruments(list_id, instruments)
        logger.info(f"{len(instruments)}個のinstrumentをリストに追加しました")

        # Create report template
        template_name = "my_eod_template"
        content_fields = data_config['report_fields']
        template_id = client.create_report_template(template_name, content_fields)
        logger.info(f"レポートテンプレートを作成しました: {template_name} (ID: {template_id})")

        # Create schedule extraction
        schedule_id = client.create_schedule_extraction(list_id, template_id)
        logger.info(f"スケジュール抽出を作成しました (ID: {schedule_id})")

        # Poll for extraction status
        status = client.get_extraction_status(schedule_id)
        while status['State'] != 'Completed':
            if status['State'] == 'Failed':
                logger.error(f"Extraction failed. Status: {status}")
                break

            logger.info(f"Extraction not completed yet. Status: {status['State']}. Waiting for 30 seconds...")
            time.sleep(30)  # Wait for 30 seconds before checking again
            status = client.get_extraction_status(schedule_id)

        if status['State'] == 'Completed':
            # Download and save extracted file
            file_id = status['Result']['FileId']
            output_path = data_config['output_path']
            client.download_extracted_file(file_id, output_path)
            logger.info(f"Downloaded and saved extracted file to: {output_path}")
        else:
            logger.error(f"Extraction did not complete successfully. Final status: {status}")

        # Download and save extracted file
        file_id = status['Result']['FileId']
        output_path = data_config['output_path']
        client.download_extracted_file(file_id, output_path)
        logger.info(f"抽出ファイルをダウンロードして保存しました: {output_path}")

    except Exception as e:
        logger.error(f"エラーが発生しました: {str(e)}")
        # TODO: Implement proper error handling and cleanup

if __name__ == "__main__":
    main()