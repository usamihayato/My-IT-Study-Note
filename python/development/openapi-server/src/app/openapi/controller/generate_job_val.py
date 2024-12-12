import lib.common.k8s_components as components
import openapi.controller.generate_job as job

from lib.common.logger import getLogger

logger = getLogger(__name__)

def call(is_local=False, **kwargs):
    logger.info('calling generate_job_val API. Make sure that this API is for valuation and is supposed to be called from Secondary AKS Cluster.')

    params = kwargs['body']

    # k8s_components 側 pod_template の VolumeClaim 設定が煩雑になるのを防ぐため、こちらで上書きする
    kwargs['body']['pod_volume_output_claim_name'] = components.override_if_exists(params, 'pod_volume_output_val_claim_name', components.POD_VOLUME_OUTPUT_VAL_CLAIM_NAME)
    return job.call(is_local=is_local, **kwargs)

if __name__ == '__main__':
    # local testing
    call(is_local=True)
