import pytest
import os
import sys
import importlib
from unittest.mock import patch
from attrdict import AttrDict

@pytest.fixture(scope='module')
def get_generate_job_module():
    ''' 事前準備. generate_job.py を import する
    '''
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__),os.pardir))
    sys.path.append(os.path.join(base_path,'src','app','openapi','controller'))
    module = importlib.import_module('generate_job')
    yield module

@pytest.fixture(scope='module')
def get_k8s_module():
    ''' 事前準備. k8s_components.py を import する
    '''
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__),os.pardir))
    sys.path.append(os.path.join(base_path,'src','lib','common'))
    module = importlib.import_module('k8s_components')
    yield module

def test_generate_job_succeed(get_generate_job_module,get_k8s_module):
    ''' Jobの作成が成功する場合
    '''
    generate_module = get_generate_job_module
    k8s_module = get_k8s_module
    params = {"job_name": "test_job"}
    status = generate_module.call(True,body=params)
    assert status[1] = 200

def test_generate_job_exception(get_generate_job_module,get_k8s_module):
    ''' Jobの作成がエラーになる場合
    '''
    generate_module = get_generate_job_module
    k8s_module = get_k8s_module
    params = {"exception": "test"}
    status = generate_module.call(True,body=params)
    assert status[1] = 500