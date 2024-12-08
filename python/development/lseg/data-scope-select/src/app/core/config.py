import os
import yaml

def get_connection_config():
    """
    接続設定を取得する。
    """
    with open('input/config/connection_config.yml', 'r') as f:
        config = yaml.safe_load(f)
    return config

def get_data_config():
    """
    データ設定を取得する。
    """
    with open('input/config/data_config.yml', 'r') as f:
        config = yaml.safe_load(f)
    return config

def get_logging_config():
    """
    ログ設定を取得する。
    """
    with open('input/config/logging_config.yml', 'r') as f:
        config = yaml.safe_load(f)
    return config