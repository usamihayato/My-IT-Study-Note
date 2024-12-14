import os
import yaml

def get_connection_config():
    """
    接続設定を取得する。
    """
    with open('input/config/connection_config.yml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config

def get_request_config():
    """リクエスト設定を取得する"""
    with open('input/config/request_config.yml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config

def get_input_path(mode: str, date: str = None) -> str:
    """入力パスを取得する"""
    request_config = get_request_config()
    base_dir = request_config['input']['base_dir']
    request_file = request_config['input']['request_file']
    if mode == 'daily':
        return os.path.join(base_dir, request_config['input']['daily_dir'], request_file)
    elif mode == 'spot':
        if not date:
            raise ValueError("スポット実行にはdate引数が必要です")
        return os.path.join(base_dir, request_config['input']['spot_dir'], date, request_file)
    else:
        raise ValueError(f"無効なmode: {mode}")

def get_output_path(mode: str, date: str) -> str:
    """出力パスを取得する"""
    request_config = get_request_config()
    base_dir = request_config['output']['base_dir']
    if mode == 'daily':
        return os.path.join(base_dir, request_config['output']['daily_dir'], date, 'data')
    elif mode == 'spot':
        return os.path.join(base_dir, request_config['output']['spot_dir'], date, 'data')
    else:
        raise ValueError(f"無効なmode: {mode}")