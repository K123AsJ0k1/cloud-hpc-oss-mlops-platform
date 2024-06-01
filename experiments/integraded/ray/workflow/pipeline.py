import logging
import time as t
from datetime import datetime

from functions.gather import gather_time

from functions.allas import setup_allas, get_object
from functions.ray import setup_ray, ray_job_handler
from functions.submission import start_slurm_job, wait_slurm_job, gather_slurm_job, get_job_artifacts, stop_proxy

def notebook_pipeline(
    allas_parameters: any,
    metadata_parameters: any,
    ray_parameters: any
):
    time_start = t.time()

    logging.basicConfig(level = logging.INFO)
    logger = logging.getLogger(__name__)

    allas_client = setup_allas(
        parameters = allas_parameters
    )
    allas_bucket = allas_parameters['allas-bucket']
    logger.info('Allas client setup')

    proxy_target = metadata_parameters['proxy-target']
    proxy_url = metadata_parameters['proxy-url']
    proxy_parameters = metadata_parameters['proxy-parameters']
    kubeflow_user = metadata_parameters['kubeflow-user']
    job_submit = metadata_parameters['job-submit']
    slurm_wait_timeout = metadata_parameters['slurm-wait-timeout']
    slurm_service_wait = metadata_parameters['slurm-service-wait']
    ray_services = metadata_parameters['ray-services']
    ray_client_timeout = metadata_parameters['ray-client-timeout']
    ray_job_path = metadata_parameters['ray-job-path']
    ray_job_envs = metadata_parameters['ray-job-envs']
    ray_job_timeout = metadata_parameters['ray-job-timeout']
    slurm_gather_timeout = metadata_parameters['slurm-gather-timeout']
    time_folder_path = metadata_parameters['time-folder-path']

    started = start_slurm_job(
        logger = logger,
        proxy_parameters = proxy_parameters,
        proxy_url = proxy_url,
        job_submit = job_submit
    )

    if started:
        slurm_job_id, slurm_job_services = wait_slurm_job(
            logger = logger,
            proxy_url = proxy_url,
            kubeflow_user = kubeflow_user,
            timeout = slurm_wait_timeout,
            wait_services = slurm_service_wait,
            target = proxy_target
        )

        logger.info('SLURM job id: ' + str(slurm_job_id))

        ray_client = setup_ray(
            logger = logger,
            services = ray_services,
            timeout = ray_client_timeout
        )
        logger.info('Ray client setup')

        ray_job_success = ray_job_handler(
            logger = logger,
            allas_client = allas_client,
            allas_bucket = allas_bucket,
            ray_client = ray_client,
            ray_parameters = ray_parameters,
            ray_job_path = ray_job_path,
            ray_job_envs = ray_job_envs,
            timeout = ray_job_timeout
        )

        logger.info('Ray job ran: ' + str(ray_job_success))

        gathered = gather_slurm_job(
            logger = logger,
            proxy_url = proxy_url,
            kubeflow_user = kubeflow_user,
            timeout = slurm_gather_timeout,
            target = proxy_target
        )

        logger.info('Slurm artifacts gathered: ' + str(gathered))
        
        if gathered:
            stop_proxy(
                proxy_url = proxy_url
            )

    time_end = t.time()

    gather_time(
        logger = logger,
        allas_client = allas_client,
        allas_bucket =  allas_bucket,
        kubeflow_user = kubeflow_user,
        time_folder_path = time_folder_path,
        object_name = 'workflow',
        action_name = 'notebook-pipeline',
        start_time = time_start,
        end_time = time_end
    )

    logger.info('Notebook pipeline complete')
         