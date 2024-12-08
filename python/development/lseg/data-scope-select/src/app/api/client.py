import os
import requests
from typing import List, Dict
from app.core.config import get_connection_config
from app.core.logger import logger

class DataScopeClient:
    def __init__(self):
        self.config = get_connection_config()
        self.base_url = self.config['base_url']
        self.headers = {'Content-Type': 'application/json; odata.metadata=minimal'}
        self.token = None

    def get_auth_token(self) -> str:
        """
        認証トークンを取得する。
        APIにログインし、認証トークンを取得して、ヘッダーに設定する。
        """
        login_data = {"Credentials": {"Password": self.config['password'], "Username": self.config['username']}}
        response = requests.post(f"{self.base_url}/Authentication/RequestToken", json=login_data, headers=self.headers)
        response.raise_for_status()
        self.token = response.json()['value']
        return self.token

    def create_instrument_list(self, name: str) -> str:
        """
        新しい銘柄リストを作成する。
        指定された名前で新しい銘柄リストを作成し、作成されたリストのIDを返す。
        """
        instrument_list_data = {
            "@odata.type": "#DataScope.Select.Api.Extractions.SubjectLists.InstrumentList",
            "Name": name
        }
        response = requests.post(f"{self.base_url}/Extractions/InstrumentLists", json=instrument_list_data, headers=self.headers)
        response.raise_for_status()
        return response.json()['ListId']

    def append_instruments(self, list_id: str, instruments: List[str]) -> None:
        """
        銘柄リストに銘柄を追加する。
        指定された銘柄リストIDに、指定された銘柄コードをリストに追加する。
        """
        instrument_list_data = {
            "Identifiers": [{"Identifier": inst, "IdentifierType": "Ric"} for inst in instruments],
            "KeepDuplicates": False
        }
        response = requests.post(f"{self.base_url}/Extractions/InstrumentLists('{list_id}')/InstrumentListAppendIdentifiers", json=instrument_list_data, headers=self.headers)
        response.raise_for_status()

    def create_report_template(self, name: str, content_fields: List[Dict[str, str]]) -> str:
        """
        新しいレポートテンプレートを作成する。
        指定された名前とコンテンツフィールドで新しいレポートテンプレートを作成し、作成されたテンプレートのIDを返す。
        """
        report_data = {
            "@odata.type": "#DataScope.Select.Api.Extractions.ReportTemplates.EndOfDayPricingReportTemplate",
            "Name": name,
            "ContentFields": [{"FieldName": field['name']} for field in content_fields]
        }
        response = requests.post(f"{self.base_url}/Extractions/ReportTemplates", json=report_data, headers=self.headers)
        response.raise_for_status()
        return response.json()['ReportTemplateId']

    def create_schedule_extraction(self, list_id: str, report_template_id: str, extraction_type: str, start_date: str = None, end_date: str = None) -> str:
        """
        データ抽出スケジュールを作成する。
        指定された銘柄リストIDとレポートテンプレートIDを使用して、データ抽出スケジュールを作成し、作成されたスケジュールのIDを返す。
        extraction_type: 'EOD' または 'Historical'
        start_date, end_date: Historicalデータ取得時の期間指定 (YYYY-MM-DD形式)
        """
        if extraction_type == 'EOD':
            schedule_data = {
                "ListId": list_id,
                "ReportTemplateId": report_template_id,
                "Recurrence": {
                    "@odata.type": "#DataScope.Select.Api.Extractions.Schedules.SingleRecurrence",
                    "ExtractionDateTime": "T00:00:00.000Z",  # Current day's data
                    "IsImmediate": False
                },
                "Trigger": {
                    "@odata.type": "#DataScope.Select.Api.Extractions.Schedules.DataAvailabilityTrigger",
                    "LimitReportToTodaysData": True
                }
            }
        elif extraction_type == 'Historical':
            if not start_date or not end_date:
                raise ValueError("start_date and end_date are required for Historical data extraction")
            
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
        else:
            raise ValueError(f"Invalid extraction_type: {extraction_type}. Must be 'EOD' or 'Historical'")

        response = requests.post(f"{self.base_url}/Extractions/Schedules", json=schedule_data, headers=self.headers)
        response.raise_for_status()
        return response.json()['ScheduleId']


    def get_extraction_status(self, schedule_id: str) -> Dict:
        """
        抽出ステータスを取得する。
        指定されたスケジュールIDの最新の抽出ステータスを取得する。
        """
        response = requests.get(f"{self.base_url}/Extractions/Schedules('{schedule_id}')/LastExtraction", headers=self.headers)
        response.raise_for_status()
        return response.json()


    def download_extracted_file(self, file_id: str, output_path: str) -> None:
        """
        抽出されたファイルをダウンロードする。
        指定されたファイルIDのデータをダウンロードし、指定されたパスに保存する。
        """
        response = requests.get(f"{self.base_url}/Extractions/ExtractedFiles('{file_id}')/$value", headers=self.headers)
        response.raise_for_status()
        with open(output_path, 'wb') as file:
            file.write(response.content)