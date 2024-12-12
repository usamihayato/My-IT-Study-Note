import pytest
import os
import sys
import importlib
import time
from unittest.mock import patch
from kubernetes import client, config
from attrdict import AttrDict

@pytest.fixture(scope='module')
def get_k8s_module():
    ''' 事前準備. k8s_components.py を import する
    '''
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__),os.pardir))
    sys.path.append(os.path.join(base_path,'src','lib','common'))
    module = importlib.import_module('k8s_components')
    yield module

@pytest.fixture(scope='module')
def get_v1_job(get_k8s_module):
    ''' 事前準備. 初期パラメータで k8s Job を作成する
    '''
    k8s_module = get_k8s_module
    params = {
        "job_name": "test-job"
    }
    # job = k8s_module._create_job_object({})
    config.load_kube_config()
    k8s_module.create_job(params)
    # batch_v1_api = client.BatchV1Api()
    # v1_job = batch_v1_api.create_namespaced_job(
    #     body = job,
    #     namespace = job.metadata.namespace
    # )
    # yield job,v1_job
    


def test_create_container_object_1(get_k8s_module):
    '''初期値で cotnainer_object を作成できることの確認
    '''
    module = get_k8s_module
    target_params = {}
    container = module.create_container_object(target_params)

    assert container.name == 'nikko-exa-batch'
    assert container.image == 'acrprivateprdje001.azurecr.io/nikko_batch:0.1.1'
    assert container.resources.requests['cpu'] is None
    assert container.resources.requests['memory'] is None
    assert container.resources.limits['cpu'] is None
    assert container.resources.limits['memory'] is None
    assert container.volume_mounts[0].name == 'batch-input'
    assert container.volume_mounts[1].name == 'batch-output'
    assert container.volume_mounts[0].mount_path == '/app/data'
    assert container.volume_mounts[1].mount_path == '/app/output'


def test_create_container_object_2(get_k8s_module):
    '''任意のパラメータを用いて cotnainer_object を作成できることの確認
    '''
    module = get_k8s_module
    target_params = {
        "job_name": "test_job_name",
        "image": "test_image:v1",
        "container_requests_cpu": "test_requests_cpu",
        "container_requests_memory": "test_requests_memory",
        "container_limits_cpu": "test_limits_cpu",
        "container_limits_memory": "test_limits_memory",
        "container_volume_mount_input_name": "test_mount_input_name",
        "container_volume_mount_input_path": "/test_mount_input_path",
        "container_volume_mount_output_name": "test_mount_output_name",
        "container_volume_mount_output_path": "/test_mount_output_path",
    }
    container = module.create_container_object(target_params)

    assert container.name == 'test_job_name'
    assert container.image == 'test_image:v1'
    assert container.resources.requests['cpu'] == 'test_requests_cpu'
    assert container.resources.requests['memory'] == 'test_requests_memory'
    assert container.resources.limits['cpu'] == 'test_limits_cpu'
    assert container.resources.limits['memory'] == 'test_limits_memory'
    assert container.volume_mounts[0].name == 'test_mount_input_name'
    assert container.volume_mounts[1].name == 'test_mount_output_name'
    assert container.volume_mounts[0].mount_path == '/test_mount_input_path'
    assert container.volume_mounts[1].mount_path == '/test_mount_output_path'


def test_create_container_object_3(get_k8s_module):
    '''サポートされていないパラメータは無視され、正常に cotnainer_object を作成できることの確認
    '''
    module = get_k8s_module
    target_params = {
        "unknown_key": "test_unknown_value"
    }
    container = module.create_container_object(target_params)

    assert container.name == 'nikko-exa-batch'
    assert container.image == 'acrprivateprdje001.azurecr.io/nikko_batch:0.1.1'
    assert container.resources.requests['cpu'] is None
    assert container.resources.requests['memory'] is None
    assert container.resources.limits['cpu'] is None
    assert container.resources.limits['memory'] is None
    assert container.volume_mounts[0].name == 'batch-input'
    assert container.volume_mounts[1].name == 'batch-output'
    assert container.volume_mounts[0].mount_path == '/app/data'
    assert container.volume_mounts[1].mount_path == '/app/output'


def test_create_pod_template_object_1(get_k8s_module):
    '''初期値で pod_object を作成できることの確認
    '''
    module = get_k8s_module
    target_params = {}
    template = module.create_pod_template_object(target_params)

    assert template.metadata.name == 'ai-analysis'
    assert template.metadata.namespace == 'openapi-app' # 固定
    assert template.metadata.labels['app'] == 'nikko-exa-batch'
    assert template.spec.restart_policy == 'OnFailure'
    assert template.spec.volumes[0].name == 'batch-input'
    assert template.spec.volumes[0].persistent_volume_claim.claim_name == 'azurefilesinputclaim'


def test_create_pod_template_object_2(get_k8s_module):
    ''' 任意のパラメータを用いて pod_object を作成できることの確認
    '''
    module = get_k8s_module
    target_params = {
        "job_name": "test_job_name",
        "pod_name": "test_pod_name",
        "pod_restart_policy": "test_pod_restart_policy",
        "pod_volume_input_name": "test_pod_volume_input_name",
        "pod_volume_input_claim_name": "test_pod_volume_input_claim_name",
    }
    template = module.create_pod_template_object(target_params)

    assert template.metadata.name == 'test_pod_name'
    assert template.metadata.namespace == 'openapi-app' # 固定

    assert template.metadata.labels['app'] == 'test_job_name'
    assert template.spec.restart_policy == 'test_pod_restart_policy'
    assert template.spec.volumes[0].name == 'test_pod_volume_input_name'
    assert template.spec.volumes[0].persistent_volume_claim.claim_name == 'test_pod_volume_input_claim_name'


def test_create_pod_template_object_3(get_k8s_module):
    '''サポートされていないパラメータは無視され、 pod_object が正常に作成できることの確認
    '''
    module = get_k8s_module
    target_params = {
        "namespace": "test_namespace",
        "unknown_key": "test_unknown_value"
    }
    template = module.create_pod_template_object(target_params)

    assert template.metadata.name == 'ai-analysis'
    assert template.metadata.namespace == 'openapi-app' # 固定
    assert template.metadata.labels['app'] == 'nikko-exa-batch'
    assert template.spec.restart_policy == 'OnFailure'
    assert template.spec.volumes[0].name == 'batch-input'
    assert template.spec.volumes[0].persistent_volume_claim.claim_name == 'azurefilesinputclaim'


def test_create_job_object_1(get_k8s_module):
    '''初期値で job_object を作成できることの確認
    '''

    module = get_k8s_module
    target_param = {} 
    job = module._create_job_object(target_param)

    assert job.api_version == 'batch/v1' # 固定
    assert job.metadata.name == 'nikko-exa-batch'
    assert job.metadata.namespace == 'openapi-app' # 固定
    assert job.spec.ttl_seconds_after_finished == 1800
    assert job.spec.backoff_limit == 6

    # pod spec / container template はすべて初期値となること
    assert job.spec.template.metadata.name == 'ai-analysis'
    assert job.spec.template.metadata.namespace == 'openapi-app'
    assert job.spec.template.metadata.labels['app'] == 'nikko-exa-batch'
    assert job.spec.template.spec.restart_policy == 'OnFailure'
    assert job.spec.template.spec.containers[0].image == 'acrprivateprdje001.azurecr.io/nikko_batch:0.1.1'
    assert job.spec.template.spec.containers[0].resources.requests['cpu'] == None
    assert job.spec.template.spec.containers[0].resources.requests['memory'] == None
    assert job.spec.template.spec.containers[0].resources.limits['cpu'] == None
    assert job.spec.template.spec.containers[0].resources.limits['memory'] == None
    assert job.spec.template.spec.containers[0].volume_mounts[0].name == 'batch-input'
    assert job.spec.template.spec.containers[0].volume_mounts[0].mount_path == '/app/data'
    assert job.spec.template.spec.volumes[0].name == 'batch-input'
    assert job.spec.template.spec.volumes[0].persistent_volume_claim.claim_name == 'azurefilesinputclaim'


def test_create_job_object_2(get_k8s_module):
    '''任意のパラメータを用いて job_object を作成できることの確認
    '''

    module = get_k8s_module
    target_param = {
        "job_name": "test_job_name",
        "job_ttl_second_after_finished": 1,
        "job_backoff_limit": 1
    } 
    job = module._create_job_object(target_param)

    assert job.api_version == 'batch/v1' # 固定
    assert job.metadata.name == 'test_job_name'
    assert job.metadata.namespace == 'openapi-app' # 固定
    assert job.spec.ttl_seconds_after_finished == 1
    assert job.spec.backoff_limit == 1

    # pod spec / container template はすべて初期値となること
    assert job.spec.template.metadata.name == 'ai-analysis'
    assert job.spec.template.metadata.namespace == 'openapi-app'
    assert job.spec.template.metadata.labels['app'] == 'test_job_name' # これは override される
    assert job.spec.template.spec.restart_policy == 'OnFailure'
    assert job.spec.template.spec.containers[0].image == 'acrprivateprdje001.azurecr.io/nikko_batch:0.1.1'
    assert job.spec.template.spec.containers[0].resources.requests['cpu'] == None
    assert job.spec.template.spec.containers[0].resources.requests['memory'] == None
    assert job.spec.template.spec.containers[0].resources.limits['cpu'] == None
    assert job.spec.template.spec.containers[0].resources.limits['memory'] == None
    assert job.spec.template.spec.containers[0].volume_mounts[0].name == 'batch-input'
    assert job.spec.template.spec.containers[0].volume_mounts[0].mount_path == '/app/data'
    assert job.spec.template.spec.volumes[0].name == 'batch-input'
    assert job.spec.template.spec.volumes[0].persistent_volume_claim.claim_name == 'azurefilesinputclaim'


def test_create_job_object_3(get_k8s_module):
    '''サポートされていないパラメータは無視され job_object が正常に作成できることの確認
    '''

    module = get_k8s_module
    target_param = {
        "api_version": "test/batch/v1",
        "namespace": "test_namespace",
        "unknown_key": "test_unknown_value"
    } 
    job = module._create_job_object(target_param)

    assert job.api_version == 'batch/v1' # 固定
    assert job.metadata.name == 'nikko-exa-batch'
    assert job.metadata.namespace == 'openapi-app' # 固定
    assert job.spec.ttl_seconds_after_finished == 1800
    assert job.spec.backoff_limit == 6

    # pod spec / container template はすべて初期値となること
    assert job.spec.template.metadata.name == 'ai-analysis'
    assert job.spec.template.metadata.namespace == 'openapi-app'
    assert job.spec.template.metadata.labels['app'] == 'nikko-exa-batch'
    assert job.spec.template.spec.restart_policy == 'OnFailure'
    assert job.spec.template.spec.containers[0].image == 'acrprivateprdje001.azurecr.io/nikko_batch:0.1.1'
    assert job.spec.template.spec.containers[0].resources.requests['cpu'] == None
    assert job.spec.template.spec.containers[0].resources.requests['memory'] == None
    assert job.spec.template.spec.containers[0].resources.limits['cpu'] == None
    assert job.spec.template.spec.containers[0].resources.limits['memory'] == None
    assert job.spec.template.spec.containers[0].volume_mounts[0].name == 'batch-input'
    assert job.spec.template.spec.containers[0].volume_mounts[0].mount_path == '/app/data'
    assert job.spec.template.spec.volumes[0].name == 'batch-input'
    assert job.spec.template.spec.volumes[0].persistent_volume_claim.claim_name == 'azurefilesinputclaim'

def test_get_job_status(get_k8s_module, get_v1_job):
    module = get_k8s_module
    params = {
        "job_name": "test-job"
    }
    #job,v1_job = get_v1_job
    batch_v1_api = client.BatchV1Api()
    batch_v1_api.delete_namespaced_job(
        name = "test-job",
        namespace = "openapi-app"
    )
    time.sleep(10)
    with pytest.raises(Exception) as e:
        job_status = module.get_job_status(params)
    assert e.typename == 'K8sOperationFailedException'
