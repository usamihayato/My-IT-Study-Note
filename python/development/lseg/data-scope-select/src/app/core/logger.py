import logging
import logging.config
import yaml

def setup_logging():
    """
    ログの設定を行う。
    """
    with open('input/config/logging_config.yml', 'r') as f:
        config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)

def get_logger(name):
    """
    ロガーを取得する。
    """
    logger = logging.getLogger(name)
    return logger