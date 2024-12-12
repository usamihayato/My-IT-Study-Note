import requests
import os
import sys
import importlib
import json
from unittest import mock
from unittest.mock import patch

def test_env(get_apiserver):
    module = get_apiserver
    assert module.conf.specs == ['api.v0']
    assert module.conf.api_specification_dir == './apispec'
    assert module.conf.enable_debugger is False
    assert module.conf.enable_swagger_ui is False
    assert module.conf.local_test_host == os.getenv('LOCAL_TEST_HOST')
    assert module.conf.local_test_port == os.getenv('LOCAL_TEST_PORT')

def test_strbool(get_serverconf):
    module = get_serverconf
    assert module._str2bool('true') is True
    assert module._str2bool('t') is True
    assert module._str2bool('1') is True
    assert module._str2bool('y') is True
    assert module._str2bool('yes') is True
    assert module._str2bool('True') is True
    assert module._str2bool('TRUE') is True
    assert module._str2bool('T') is True
    assert module._str2bool('Y') is True
    assert module._str2bool('YES') is True
    assert module._str2bool('Yes') is True
    assert module._str2bool('false') is False

def test_strlist(get_serverconf):
    module = get_serverconf
    assert module._str2list("[api.v0]") == ['api.v0']
    assert module._str2list("['api.v0']") == ['api.v0']
    assert module._str2list("[\"api.v0\"]") == ['api.v0']
    assert module._str2list("[\'api.v0\']") == ['api.v0']
    assert module._str2list('[api.v0]') == ['api.v0']
    assert module._str2list('["api.v0"]') == ['api.v0']
    assert module._str2list('[\"api.v0\"]') == ['api.v0']
    assert module._str2list('[\'api.v0\']') == ['api.v0']
    assert module._str2list("['api.v0','api.v1']") == ['api.v0','api.v1']

def test_health(get_apiserver):
    module = get_apiserver
    client = module.application.test_client()
    response = client.get('/api/v0/health')
    assert response.status_code == 200

def test_generate(get_apiserver):
    module = get_apiserver
    client = module.application.test_client()
    payload = json.dumps({'job_name':'batch'})
    response = client.post('/api/v0/generate_job',data=payload,content_type='application/json')
    assert response.status_code == 200

def test_job_status(get_apiserver):
    module = get_apiserver
    client = module.application.test_client()
    payload = json.dumps({'job_name':'batch'})
    response = client.post('/api/exa/v1/job_status',data=payload,content_type='application/json')
    assert response.status_code == 200