import pytest
import os
import sys
import importlib
from unittest.mock import patch
from attrdict import AttrDict

@pytest.fixture(scope='module')
def get_job_status_module():
    ''' 事前準備. job_status.py を import する
    '''
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__),os.pardir))
    sys.path.append(os.path.join(base_path,'src','app','openapi','controller'))
    module = importlib.import_module('job_status')
    yield module

@pytest.fixture(scope='module')
def get_k8s_module():
    ''' 事前準備. k8s_components.py を import する
    '''
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__),os.pardir))
    sys.path.append(os.path.join(base_path,'src','lib','common'))
    module = importlib.import_module('k8s_components')
    yield module

def test_job_status_succeeded(get_job_status_module,get_k8s_module):
    ''' Jobが完了した場合
    '''
    job_status_module = get_job_status_module
    k8s_module = get_k8s_module
    job_status =AttrDict({'status':{'succeeded':1,'failed':0}})
    with patch.object(k8s_module,'get_job_status',return_value=job_status):
        status = job_status_module.call(True,body=None)
        assert status[1] = 200

def test_job_status_failed(get_job_status_module,get_k8s_module):
    ''' backoff_limmit等でJobが失敗する場合
    '''
    job_status_module = get_job_status_module
    k8s_module = get_k8s_module
    job_status =AttrDict({'status':{'succeeded':0,'failed':1}})
    with patch.object(k8s_module,'get_job_status',return_value=job_status):
        status = job_status_module.call(True,body=None)
        assert status[1] = 500

def test_job_status_none(get_job_status_module,get_k8s_module):
    ''' 存在しない job をリクエストした場合
    '''
    job_status_module = get_job_status_module
    k8s_module = get_k8s_module
    with patch.object(k8s_module,'get_job_status',return_value=None):
        status = job_status_module.call(True,body=None)
        assert status[1] = 500

def test_job_status_running(get_job_status_module,get_k8s_module):
    ''' Jobがランニングの場合
    '''
    job_status_module = get_job_status_module
    k8s_module = get_k8s_module
    job_status =AttrDict({'status':{'succeeded':0,'failed':0}})
    with patch.object(k8s_module,'get_job_status',return_value=job_status):
        status = job_status_module.call(True,body=None)
        assert status[1] = 200