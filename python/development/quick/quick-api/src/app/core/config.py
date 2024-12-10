import yaml

def get_connection_config():
    """
    接続設定を取得する。
    """
    with open('input/config/connection_config.yml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config