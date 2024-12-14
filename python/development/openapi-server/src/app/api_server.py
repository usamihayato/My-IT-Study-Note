import connexion

from lib.common.logger import getLogger
from serverconf import DMDataAnalyticsServerConf

logger = getLogger('ApiServerMain')


def setup(conf: DMDataAnalyticsServerConf):
    server = connexion.App(
        __name__,
        host=conf.local_test_host,
        port=conf.local_test_port,
        specification_dir=conf.api_specification_dir,
        debug=conf.enable_debugger,
        options={
            'swagger_ui': conf.enable_swagger_ui,
        },
    )
    for spec in conf.specs:
        server.add_api(f'{spec}.yml', validate_responses=True)
    return server

conf = DMDataAnalyticsServerConf().load()
app = setup(conf)
application = app.app