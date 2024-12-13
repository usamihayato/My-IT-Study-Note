from flask import Flask, jsonify, request
import json
import os
from collections import defaultdict

app = Flask(__name__)

# トークンエンドポイントのハンドラーを追加
@app.route('/v2/token', methods=['POST'])
def get_token():
    response = {
        "access_token": "SECRET_TOKEN_GOES_HERE",
        "token_type": "Bearer",
        "expires_in": 1079,
        "scope": "offline documents_and_images_read documents_and_images_write saved_content_read saved_content_write automations_execute automations_read automations_write journeys_execute journeys_read journeys_write email_read email_send email_write push_read push_send push_write sms_read sms_send sms_write social_post social_publish social_read social_write web_publish web_read web_write audiences_read audiences_write list_and_subscribers_read list_and_subscribers_write data_extensions_read data_extensions_write file_locations_read file_locations_write tracking_events_read calendar_read calendar_write campaign_read campaign_write accounts_read accounts_write users_read users_write webhooks_read webhooks_write workflows_write approvals_write tags_write approvals_read tags_read workflows_read ott_chat_messaging_read ott_chat_messaging_send ott_channels_read ott_channels_write marketing_cloud_connect_read marketing_cloud_connect_write marketing_cloud_connect_send event_notification_callback_create event_notification_callback_read event_notification_callback_update event_notification_callback_delete event_notification_subscription_create event_notification_subscription_read event_notification_subscription_update event_notification_subscription_delete",
        "soap_instance_url": "https://mcmtwjynv76zg4b73149z7yzw5mm.soap.marketingcloudapis.com/",
        "rest_instance_url": "https://mcmtwjynv76zg4b73149z7yzw5mm.rest.marketingcloudapis.com/"
    }
    return jsonify(response)

def load_postman_collection(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_endpoints(collection):
    endpoints = defaultdict(list)
    
    def process_item(item):
        if 'request' in item and 'response' in item:
            method = item['request']['method']
            path = item['request'].get('url', {}).get('path', '')
            response = item['response'][0].get('body') if item.get('response') else None
            
            # パスをstring形式に変換
            if isinstance(path, list):
                path = '/' + '/'.join(path)
            
            # メソッドとパスの組み合わせをキーとして使用
            endpoint_key = f"{method}_{path}"
            endpoints[endpoint_key].append({
                'method': method,
                'path': path,
                'response': response
            })
            
        elif 'item' in item:
            for sub_item in item['item']:
                process_item(sub_item)
    
    if 'item' in collection:
        for item in collection['item']:
            process_item(item)
            
    return endpoints

class MockAPI:
    def __init__(self, postman_json_path):
        self.collection = load_postman_collection(postman_json_path)
        self.endpoints = extract_endpoints(self.collection)
        
    def register_routes(self, app):
        registered_endpoints = set()
        
        for endpoint_key, endpoint_list in self.endpoints.items():
            # 各エンドポイントの最初のエントリのみを使用
            endpoint = endpoint_list[0]
            route = endpoint['path']
            
            if endpoint_key in registered_endpoints:
                print(f"Warning: Skipping duplicate endpoint: {endpoint_key}")
                continue
                
            def create_handler(response_data):
                def handler():
                    return jsonify(response_data)
                return handler
            
            print(f"Registering endpoint: {endpoint['method']} {route}")
            
            try:
                app.add_url_rule(
                    route,
                    endpoint_key,
                    create_handler(endpoint['response']),
                    methods=[endpoint['method']]
                )
                registered_endpoints.add(endpoint_key)
            except AssertionError as e:
                print(f"Error registering endpoint {endpoint_key}: {str(e)}")
                continue

def main():
    # Postman CollectionのJSONファイルパスを指定
    current_dir = os.path.dirname(os.path.abspath(__file__))
    postman_json_path = os.path.join(current_dir, 'postman_collection.json')
    
    if not os.path.exists(postman_json_path):
        print(f"Error: Postman collection file not found at {postman_json_path}")
        return
    
    try:
        # MockAPIのインスタンス作成
        mock_api = MockAPI(postman_json_path)
        
        # ルートの登録
        mock_api.register_routes(app)
        
        # サーバーの起動
        print("Starting mock server on http://localhost:5000")
        app.run(debug=True, port=5000)
        
    except Exception as e:
        print(f"Error starting mock server: {str(e)}")

if __name__ == '__main__':
    main()