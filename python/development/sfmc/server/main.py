from flask import Flask, jsonify, request
import json
import os

app = Flask(__name__)

def load_postman_collection(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_endpoints(collection):
    endpoints = []
    
    def process_item(item):
        if 'request' in item and 'response' in item:
            endpoint = {
                'method': item['request']['method'],
                'path': item['request'].get('url', {}).get('path', ''),
                'response': item['response'][0].get('body') if item['response'] else None
            }
            endpoints.append(endpoint)
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
        for endpoint in self.endpoints:
            route = '/' + '/'.join(endpoint['path']) if isinstance(endpoint['path'], list) else endpoint['path']
            
            def create_handler(response_data):
                def handler():
                    return jsonify(response_data)
                return handler
            
            app.add_url_rule(
                route,
                f"{endpoint['method']}_{route}",
                create_handler(endpoint['response']),
                methods=[endpoint['method']]
            )

if __name__ == '__main__':
    # Postman CollectionのJSONファイルパスを指定
    postman_json_path = 'postman/sfmc_postman_collection.json'
    
    # MockAPIのインスタンス作成
    mock_api = MockAPI(postman_json_path)
    
    # ルートの登録
    mock_api.register_routes(app)
    
    # サーバーの起動
    app.run(debug=True, port=5000)