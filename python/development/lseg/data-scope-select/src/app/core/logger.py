import logging
import logging.config
import yaml

def setup_logging(config_path):
    """
    ログの設定を行う。
    """
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)

def get_logger(name):
    """
    ロガーを取得する。
    """
    logger = logging.getLogger(name)
    return logger