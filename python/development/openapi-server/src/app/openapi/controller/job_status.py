import lib.common.k8s_components as components
from kubernetes import config

from lib.common.logger import getLogger
logger = getLogger(__name__)


def job_has_completed(params=None):
    completed = False
    job_status = components.get_job_status(params) # can throw K8sOperationFailedException

    if job_status is None:
        # 存在しない job をリクエストした場合などは get_job_status が exception を throw するため、ここには入らない想定
        raise components.K8sOperationFailedException('unexpectedly k8s_components.get_job_status operation has failed. should check previous processes or errors occurred')

    if job_status.status.failed == 1:
        raise components.K8sOperationFailedException('job failed as backoffLimit has been reached.')

    if job_status.status.succeeded == 1:
        completed = True

    return completed


def call(is_local=False, **kwargs):
    logger.info('calling job_stats API.')

    if is_local:
        config.load_kube_config()
    else:
        # Service Account が作成され、 ClusterRoleBinding されている前提
        config.load_incluster_config()

    # 常に存在する
    params = kwargs['body']

    try:
        if job_has_completed(params):
            logger.info('job has successfully completed')
            return {'result': 'job completed'}, 200
    except components.K8sOperationFailedException as e:
        logger.exception(f'{e}')
        return {'result': 'failed'}, 500
    else:
        return {'result': 'job running'}, 200


if __name__ == '__main__':
    # local testing
    call(is_local=True)
