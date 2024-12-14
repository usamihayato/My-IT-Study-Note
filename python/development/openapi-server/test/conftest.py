import pytest
import importlib
import os
import sys
import json
import kubernetes
from kubernetes import client, config
from unittest.mock import patch
from attrdict import AttrDict

def pytest_addoption(parser):
    parser.addoption(
        "--local",
        action="store_true",
        default=False,
        help="set local endpoint"
    )
    parser.addoption(
        '--env',
        action='store',
        default='itg',
        help='set env'
    )

@pytest.fixture()
def get_apiserver():
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__),os.pardir))
    sys.path.append(os.path.join(base_path,'src','lib','common'))
    k8s_module = importlib.import_module('k8s_components')
    job_status = AttrDict({'status':{'succeeded':1,'failed':1}})
    with patch.object(config,'load_incluster_config'):
        with patch.object(k8s_module,'create_job_object'):
            with patch.object(client,'BatchV1Api'):
                with patch.object(k8s_module,'get_job_status',return_value=job_status):
                    sys.path.append(os.path.join(base_path,'src','app'))
                    module = importlib.import_module('api_server')
                    yield module

@pytest.fixture()
def get_serverconf():
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__),os.pardir))
    sys.path.append(os.path.join(base_path,'src','app'))
    module = importlib.import_module('serverconf')
    yield module

@pytest.fixture(scope='session', autouse=True)
def cmdopt(request):
    os.environ['ENV'] = request.config.getoption("--env")
    if(request.config.getoption("--local")):
        set_environment_variable('variable.local.json')
    else:
        set_environment_variable('variable.json')

def set_environment_variable(json_filepath):
    with open(f"{json_filepath}") as filedata:
        for key, value in json.load(filedata).items():
            os.environ[key] = value