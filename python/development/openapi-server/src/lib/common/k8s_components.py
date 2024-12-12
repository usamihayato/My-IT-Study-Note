from typing import Any

from kubernetes import client
from kubernetes.client.rest import ApiException

from lib.common.logger import getLogger
logger = getLogger(__name__)

CONTAINER_REQUESTS_CPU=None # TODO: 要チューニング
CONTAINER_REQUESTS_MEMORY=None # TODO: 要チューニング
CONTAINER_LIMITS_CPU=None # TODO: 要チューニング
CONTAINER_LIMITS_MEMORY=None # TODO: 要チューニング
CONTAINER_VOLUME_MOUNT_INPUT_NAME="batch-input"
CONTAINER_VOLUME_MOUNT_INPUT_PATH="/app/data"
CONTAINER_VOLUME_MOUNT_OUTPUT_NAME="batch-output"
CONTAINER_VOLUME_MOUNT_OUTPUT_PATH="/app/output"
CONTAINER_IMAGE="acrprivateprdje001.azurecr.io/nikko_batch:0.1.1"
CONTAINER_IMAGE_PULL_POLICY="Always"

POD_NAME="ai-analysis"
POD_NAMESPACE="openapi-app"
POD_RESTART_POLICY="OnFailure"
POD_VOLUME_INPUT_NAME="batch-input"
POD_VOLUME_INPUT_CLAIM_NAME="azurefilesinputclaim"
POD_VOLUME_OUTPUT_NAME="batch-output"
POD_VOLUME_OUTPUT_CLAIM_NAME="azurefilesoutputclaim"
POD_VOLUME_OUTPUT_VAL_CLAIM_NAME="azurefilesoutputvalclaim"

JOB_BACKOFF_LIMIT=6
JOB_TTL_SECOND_AFTER_FINISHED=1800

API_VERSION = "batch/v1"
JOB_NAME = "nikko-exa-batch"
JOB_NAMESPACE = "openapi-app"

READ_REQUEST_TIMEOUT = 60

class K8sOperationFailedException(Exception):
    def __init__(self, msg):
        super().__init__(msg)


def override_if_exists(params:dict, key:str ,default:Any):
    return default if key not in params else params[key]


def create_container_object(params):
    job_name=override_if_exists(params, "job_name", JOB_NAME)
    image=override_if_exists(params, "image", CONTAINER_IMAGE)
    container_image_pull_policy=override_if_exists(params, "container_image_pull_policy", CONTAINER_IMAGE_PULL_POLICY)
    container_requests_cpu=override_if_exists(params, "container_requests_cpu", CONTAINER_REQUESTS_CPU)
    container_requests_memory=override_if_exists(params, "container_requests_memory", CONTAINER_REQUESTS_MEMORY)
    container_limits_cpu=override_if_exists(params, "container_limits_cpu", CONTAINER_LIMITS_CPU)
    container_limits_memory=override_if_exists(params, "container_limits_memory", CONTAINER_LIMITS_MEMORY)
    container_volume_mount_input_name=override_if_exists(params, "container_volume_mount_input_name", CONTAINER_VOLUME_MOUNT_INPUT_NAME)
    container_volume_mount_input_path=override_if_exists(params, "container_volume_mount_input_path", CONTAINER_VOLUME_MOUNT_INPUT_PATH)
    container_volume_mount_output_name=override_if_exists(params, "container_volume_mount_output_name", CONTAINER_VOLUME_MOUNT_OUTPUT_NAME)
    container_volume_mount_output_path=override_if_exists(params, "container_volume_mount_output_path", CONTAINER_VOLUME_MOUNT_OUTPUT_PATH)

    container = client.V1Container(
        command=["sh", "scripts/run.sh"], # ExaWizards コンテナ の仕様に依存
        name=job_name,
        image=image,
        image_pull_policy=container_image_pull_policy,
        resources=client.V1ResourceRequirements(
            requests={
                "cpu": container_requests_cpu,
                "memory": container_requests_memory
            },
            limits={
                "cpu": container_limits_cpu,
                "memory": container_limits_memory
            }
        ),
        volume_mounts=[
            client.V1VolumeMount(
                name=container_volume_mount_input_name,
                mount_path=container_volume_mount_input_path,
            ),
            client.V1VolumeMount(
                name=container_volume_mount_output_name,
                mount_path=container_volume_mount_output_path,
            )
        ]
    )
    
    return container


def create_pod_template_object(params):
    # 基本パラメータ
    job_name = override_if_exists(params, "job_name", JOB_NAME)
    pod_name = override_if_exists(params, "pod_name", POD_NAME)
    pod_namespace = POD_NAMESPACE  # pvc と secret が JOB_NAMESPACE で作成されているため固定
    pod_restart_policy = override_if_exists(params, "pod_restart_policy", POD_RESTART_POLICY)
    
    # ボリューム関連の設定
    mount_config = params.get('mount_config', {})
    storage_config = mount_config.get('storage_config', {})
    
    # 入力ボリューム設定
    pod_volume_input_name = override_if_exists(params, "pod_volume_input_name", POD_VOLUME_INPUT_NAME)
    pod_volume_input_claim_name = storage_config.get('input_claim_name', 
        override_if_exists(params, "pod_volume_input_claim_name", POD_VOLUME_INPUT_CLAIM_NAME))
    
    # 出力ボリューム設定
    pod_volume_output_name = override_if_exists(params, "pod_volume_output_name", POD_VOLUME_OUTPUT_NAME)
    pod_volume_output_claim_name = storage_config.get('output_claim_name',
        override_if_exists(params, "pod_volume_output_claim_name", POD_VOLUME_OUTPUT_CLAIM_NAME))
    
    # DNS設定
    dns_config = params.get('dns_config')
    pod_dns_config = None
    if dns_config:
        pod_dns_config = client.V1PodDNSConfig(**dns_config)

    # コンテナにマウントパス情報を渡すために params を更新
    if mount_config:
        params['mount_config'] = mount_config

    template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(
            name=pod_name,
            namespace=pod_namespace,
            labels={
                "app": job_name,
            }
        ),
        spec=client.V1PodSpec(
            restart_policy=pod_restart_policy,
            dns_config=pod_dns_config,  # DNS設定を追加
            containers=[create_container_object(params)],
            volumes=[
                client.V1Volume(
                    name=pod_volume_input_name,
                    persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(
                        claim_name=pod_volume_input_claim_name
                    )
                ),
                client.V1Volume(
                    name=pod_volume_output_name,
                    persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(
                        claim_name=pod_volume_output_claim_name
                    )
                ),
            ]
        )
    )

    return template


def _create_job_object(params):
    job_name=override_if_exists(params, "job_name", JOB_NAME)
    job_namespace=JOB_NAMESPACE # pvcとsecretがJOB_NAMESPACEで作成されているため固定
    job_ttl_second_after_finished=override_if_exists(params, "job_ttl_second_after_finished", JOB_TTL_SECOND_AFTER_FINISHED)
    job_backoff_limit=override_if_exists(params, "job_backoff_limit", JOB_BACKOFF_LIMIT)

    spec = client.V1JobSpec(
        ttl_seconds_after_finished=job_ttl_second_after_finished,
        template=create_pod_template_object(params),
        backoff_limit=job_backoff_limit)

    # api_versionはbatch/v1のみ使用
    job = client.V1Job(
        api_version=API_VERSION,
        kind="Job",
        metadata=client.V1ObjectMeta(name=job_name, namespace=job_namespace),
        spec=spec)

    return job


def create_job(params):
    # api_versionはbatch/v1のみ使用
    batch_v1_api = client.BatchV1Api()
    job_obj = _create_job_object(params)

    try:
        v1_job = batch_v1_api.create_namespaced_job(
            body=job_obj,
            namespace=job_obj.metadata.namespace)
    except ApiException as e:
        raise K8sOperationFailedException("[create_namespaced_job] couldn't crate job: %s\n" )
    else:
        logger.info("Job created. status='%s'" % str(v1_job.status))


def get_job_status(params):
    job_name=override_if_exists(params, "job_name", JOB_NAME)
    job_namespace=JOB_NAMESPACE # pvcとsecretが JOB_NAMESPACE で作成されているため固定
    request_timeout = override_if_exists(params, 'request_timeout', READ_REQUEST_TIMEOUT)

    # api_versionはbatch/v1のみ使用
    batch_v1_api = client.BatchV1Api()

    job_status = None
    try:
        job_status = batch_v1_api.read_namespaced_job_status(
            name=job_name,
            namespace=job_namespace,
            # ADF WEB アクティビティのタイムアウトが 60 秒であり、 ADF 経由で実行する限りにおいて request_timeout > 60 は意味をなさない
            _request_timeout=(request_timeout,),
            pretty=True)

    except ApiException as e: # ネットワーク疎通の失敗でタイムアウトしたとき / 存在しない Job をリクエストしたとき
        raise K8sOperationFailedException("[read_namespaced_job] couldn't get job_status: %s\n" )
    else:
        return job_status
