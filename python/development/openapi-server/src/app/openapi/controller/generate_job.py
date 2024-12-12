import lib.common.k8s_components as components
from kubernetes import config

from lib.common.logger import getLogger
logger = getLogger(__name__)

def call(is_local=False, **kwargs):
    logger.info('calling generate_job API. Make sure that this API is for production and is supposed to be called from Primary AKS Cluster.')

    if is_local:
        config.load_kube_config()
    else:
        # Service Account が作成され、 ClusterRoleBinding されている前提
        config.load_incluster_config()

    # 常に存在する
    params = kwargs['body']
    try:
        components.create_job(params)
    except components.K8sOperationFailedException as e:
        logger.exception(f'{e}')
        return {'result': 'failed'}, 500

    logger.info("Batch Job has successfully finished.")
    return {'result': 'succeed'}, 200

if __name__ == '__main__':
    # local testing
    call(is_local=True)
