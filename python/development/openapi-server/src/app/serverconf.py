import configparser
import os

from lib.common.logger import getLogger

logger = getLogger(__name__)
CONF = 'serverconf.ini'

def _str2bool(s):
    logger.info(f'converting {s} to bool')
    return s.lower() in ['true', 't', '1', 'y', 'yes']

def _str2list(s):
    logger.info(f'converting {s} to list')

    s = s.replace('\'', '')
    s = s.replace('"', '')

    _l = []
    for _s in s:
        if _s == '[':
            _l.append(_s)
            _l.append('\'')
        elif _s == ']':
            _l.append('\'')
            _l.append(_s)
        elif _s == ',': 
            _l.append(',')
            _l.append(_s)
            _l.append(',')
        else:
            _l.append(_s)
    return eval("".join(_l))



class MissingRequiredParamsException(Exception):
    def __init__(self, fields):
        message = f'parameters {fields} required. must set in ENV or {CONF}'
        super().__init__(message)


class DMDataAnalyticsServerConf():
    CONF_INI = os.path.join(os.path.abspath(os.path.dirname(__file__)), CONF)

    # ここに定義したもの以外は受け付けない
    conf_attributes = {
        'api_specification_dir': ('str', 'API_SPECIFICATION_DIR', True), # required
        'specs': ('list', 'SPECS', True), # required
        'enable_debugger': ('bool', 'ENABLE_DEBUGGER', False),
        'enable_swagger_ui': ('bool', 'ENABLE_SWAGGER_UI', False),
        'local_test_host': ('str', 'LOCAL_TEST_HOST', False),
        'local_test_port': ('str', 'LOCAL_TEST_PORT', False),
    }

    def __init__(self, api_specification_dir=None, specs=None, enable_debugger=False, enable_swagger_ui=False, local_test_host=None, local_test_port=None):
        self._api_specification_dir = api_specification_dir
        self._specs = specs
        self._enable_debugger = enable_debugger
        self._enable_swagger_ui = enable_swagger_ui
        self._local_test_host = local_test_host
        self._local_test_port = local_test_port

    # setter は不要なため定義しない

    @property
    def api_specification_dir(self):
        return self._api_specification_dir
    
    @property
    def specs(self):
        return self._specs
    
    @property
    def enable_debugger(self):
        return self._enable_debugger
    
    @property
    def enable_swagger_ui(self):
        return self._enable_swagger_ui
    
    @property
    def local_test_host(self):
        return self._local_test_host
    
    @property
    def local_test_port(self):
        return self._local_test_port

    @classmethod
    def load(cls, ini=CONF_INI):
        conf = cls.load_from_config(ini)
        conf.update(cls.load_from_env())

        missings = []
        for _attr, _map in cls.conf_attributes.items():
            if _map[2] and _attr not in conf:
                missings.append(_attr)
            
        if len(missings) > 0:
            raise MissingRequiredParamsException(missings)

        return DMDataAnalyticsServerConf(**conf)

    @classmethod
    def load_from_config(cls, ini):
        conf_dict = {}

        conf = configparser.ConfigParser()
        conf.read(ini, encoding='utf8')

        sections = conf.sections()

        for section in sections:
            for option in conf.options(section):
                if option not in cls.conf_attributes:
                    logger.warning(f'skipped loading option: [{option}] is not supported')
                    continue

                _type = cls.conf_attributes.get(option)[0]

                # あと勝ちで override
                if _type == 'bool':
                    conf_dict[option] = conf.getboolean(section, option)
                
                elif _type == 'list':
                    v = conf.get(section, option)
                    conf_dict[option] = _str2list(v)

                else:
                    conf_dict[option] = conf.get(section, option)
                
        return conf_dict

    @classmethod
    def load_from_env(cls):

        _env = os.environ
        conf_dict = {}

        for _attr, _map  in cls.conf_attributes.items():
            v = _env.get(_map[1]) # default: None

            if v:
                _type = _map[0]
                if _type == 'bool':
                    conf_dict[_attr] = _str2bool(v)
                elif _type == 'list':
                    conf_dict[_attr] = _str2list(v)
                else:
                    conf_dict[_attr] = v
                logger.info(f'uwsgi parameter: [{_attr}] retrieved from container env')
        
        return conf_dict


# if __name__ == '__main__':
#     conf = DMDataAnalyticsServerConf().load()
#     print(conf.__dict__)
