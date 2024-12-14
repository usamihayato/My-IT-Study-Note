from flask import Flask, jsonify, request, Blueprint
from flask_cors import CORS
import json
import os
from collections import defaultdict

class MockAPI:
    """SFMC API モックサーバー"""
    
    def __init__(self, postman_json_path: str):
        """
        PostmanコレクションからモックAPIを初期化
        
        Args:
            postman_json_path (str): Postmanコレクションのファイルパス
        """
        self.collection = self._load_postman_collection(postman_json_path)
        self.rest_endpoints = defaultdict(list)
        self.soap_endpoints = defaultdict(list)
        self._extract_endpoints()

    def _load_postman_collection(self, file_path: str) -> dict:
        """Postmanコレクションを読み込む"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _extract_endpoints(self) -> None:
        """コレクションからエンドポイントを抽出"""
        def process_item(item):
            if 'request' in item and 'response' in item:
                method = item['request']['method']
                path = item['request'].get('url', {}).get('path', '')
                response = item['response'][0].get('body') if item.get('response') else None
                
                # パスをstring形式に変換
                if isinstance(path, list):
                    path = '/' + '/'.join(path)
                elif not path.startswith('/'):
                    path = '/' + path
                
                # SOAP APIのパスを正規化
                if path.endswith('.asmx'):
                    path = path.replace('.asmx', '/soap')
                
                # エンドポイント情報を作成
                endpoint_data = {
                    'method': method,
                    'path': path,
                    'response': response
                }
                
                # URLからAPIタイプを判断してエンドポイントを振り分け
                endpoint_key = method + path
                if 'soap' in path.lower():
                    self.soap_endpoints[endpoint_key].append(endpoint_data)
                else:
                    self.rest_endpoints[endpoint_key].append(endpoint_data)
                
            elif 'item' in item:
                for sub_item in item['item']:
                    process_item(sub_item)
        
        if 'item' in self.collection:
            for item in self.collection['item']:
                process_item(item)


def register_endpoint(blueprint, endpoint_data):
    """ブループリントにエンドポイントを登録"""
    def create_handler(response_data):
        def handler():
            return jsonify(response_data)
        return handler

    method = endpoint_data['method']
    path = endpoint_data['path']
    response = endpoint_data['response']

    # エンドポイントキーの作成（ドットを除去し、一意性を確保）
    safe_path = path.replace('.', '_dot_')  # .asmx → _dot_asmx
    endpoint_key = f"{method}_{safe_path}_{hash(str(response))}"[:100]  # キーの長さを制限

    try:
        # 既に登録されているかチェック
        if endpoint_key in blueprint.view_functions:
            print(f"Warning: Endpoint already exists, skipping: {method} {path}")
            return

        blueprint.add_url_rule(
            path,
            endpoint_key,
            create_handler(response),
            methods=[method]
        )
        print(f"Registered {method} {path} on {blueprint.url_prefix}")
    except Exception as e:
        print(f"Error registering endpoint {method} {path}: {str(e)}")


def create_mock_server():
    """モックサーバーのFlaskアプリケーションを作成"""
    app = Flask(__name__)
    CORS(app)

    # REST API, SOAP API, Auth API用のBlueprintを作成
    rest_api = Blueprint('rest_api', __name__, url_prefix='/rest')
    soap_api = Blueprint('soap_api', __name__, url_prefix='/soap')
    auth_api = Blueprint('auth_api', __name__, url_prefix='/auth')

    # トークンエンドポイントのハンドラー（認証用）
    @auth_api.route('/v2/token', methods=['POST'])
    def get_token():
        response = {
            "access_token": "MOCK_TOKEN",
            "token_type": "Bearer",
            "expires_in": 1079,
            "scope": "all_endpoints",
            "soap_instance_url": "http://localhost:5000/soap",
            "rest_instance_url": "http://localhost:5000/rest"
        }
        return jsonify(response)

    return app, rest_api, soap_api, auth_api


def setup_mock_server(postman_json_path):
    """モックサーバーのセットアップを行う"""
    # モックAPIのインスタンス作成
    mock_api = MockAPI(postman_json_path)
    
    # Flaskアプリケーションとブループリントの作成
    app, rest_api, soap_api, auth_api = create_mock_server()
    
    # 登録済みエンドポイントを追跡
    registered_endpoints = set()
    
    # RESTエンドポイントの登録
    for key, endpoints in mock_api.rest_endpoints.items():
        # 重複するエンドポイントの場合、最初のものだけを使用
        if key not in registered_endpoints:
            register_endpoint(rest_api, endpoints[0])
            registered_endpoints.add(key)
    
    # SOAPエンドポイントの登録
    for key, endpoints in mock_api.soap_endpoints.items():
        if key not in registered_endpoints:
            register_endpoint(soap_api, endpoints[0])
            registered_endpoints.add(key)
    
    # ブループリントの登録（auth_apiを最初に登録）
    app.register_blueprint(auth_api)
    app.register_blueprint(rest_api)
    app.register_blueprint(soap_api)
    
    return app


def main():
    """メイン実行関数"""
    # Postman CollectionのJSONファイルパスを指定
    current_dir = os.path.dirname(os.path.abspath(__file__))
    postman_json_path = os.path.join(current_dir, 'postman_collection.json')
    
    if not os.path.exists(postman_json_path):
        print(f"Error: Postman collection file not found at {postman_json_path}")
        return
    
    try:
        app = setup_mock_server(postman_json_path)
        print("Starting mock server with multiple endpoints on http://localhost:5000")
        print("Auth API available at: http://localhost:5000/auth")
        print("REST API available at: http://localhost:5000/rest")
        print("SOAP API available at: http://localhost:5000/soap")
        app.run(debug=True, port=5000)
        
    except Exception as e:
        print(f"Error starting mock server: {str(e)}")


if __name__ == '__main__':
    main()