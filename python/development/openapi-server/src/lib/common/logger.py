import os
from logging import config

LOGGER_CONF = 'logger.conf'
file_dir = os.path.dirname(os.path.abspath(__file__))

def getLogger(name, id_debug_enagled=False):
    from logging import getLogger
    config.fileConfig(
        os.path.join(file_dir, LOGGER_CONF),
        disable_existing_loggers=False # avoid overriding existing logger settings
    )

    return getLogger(name)

#TODO Debug ログの有効化関数
