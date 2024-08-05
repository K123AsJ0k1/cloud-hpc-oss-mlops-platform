import os
import json
import time as t

from allas import get_object 
from porter import test_url

from ray.job_submission import JobSubmissionClient
from ray.job_submission import JobStatus

'''RAY'''
def setup_ray(
    logger: any,
    services: any,
    timeout: int
):
    logger.info('Setting up ray client')
    start = t.time()
    ray_client = None
    if 0 < len(services):
        ray_dashboard_url = 'http://' + services['ray-dashboard']
        ray_exists = None
        while t.time() - start <= timeout:
            logger.info('Testing ray client url: ' + str(ray_dashboard_url))
            ray_exists = test_url(
                target_url = ray_dashboard_url,
                timeout = 5
            )
            logger.info('Ray client exists: ' + str(ray_exists))
            if ray_exists:
                break
            t.sleep(5)
        if ray_exists:
            ray_client = JobSubmissionClient(
                address = ray_dashboard_url
            )
            logger.info("Ray setup")
    return ray_client

def get_ray_job(
    logger: any,
    allas_client: any,
    allas_bucket: str,
    ray_job_path: str
) -> any:
    logger.info('Ray job path:' + str(ray_job_path))
    ray_job = get_object(
        client = allas_client,
        bucket_name = allas_bucket,
        object_path = ray_job_path
    )

    ray_job_name = ray_job_path.split('/')[-1]

    current_directory = os.getcwd()
    ray_job_directory = os.path.join(current_directory, 'jobs')

    if not os.path.exists(ray_job_directory):
        logger.info('Make directory')
        os.makedirs(ray_job_directory)
    
    ray_job_file = ray_job_name + '.py'
    used_ray_job_path = os.path.join(ray_job_directory, ray_job_file)
    
    logger.info('Job writing path:' + str(used_ray_job_path))
    with open(used_ray_job_path, 'w') as file:
        file.write(ray_job)

    return ray_job_file, ray_job_directory

def submit_ray_job(
    logger: any,
    ray_client: any,
    ray_parameters: any,
    job_file: any,
    working_directory: str,
    job_envs: any
) -> any:
    logger.info('Submitting ray job ' + str(job_file) + ' using directory ' + str(working_directory))
    command = "python " + str(job_file)
    if 0 < len(ray_parameters):
        command = command + " '" + json.dumps(ray_parameters) + "'"
    job_id = ray_client.submit_job(
        entrypoint = command,
        runtime_env = {
            'working_dir': str(working_directory),
            'env_vars': job_envs
        }
    )
    return job_id

def wait_ray_job(
    logger: any,
    ray_client: any,
    ray_job_id: int, 
    waited_status: any,
    timeout: int
) -> any:
    logger.info('Waiting ray job ' + str(ray_job_id))
    start = t.time()
    job_status = None
    while t.time() - start <= timeout:
        status = ray_client.get_job_status(ray_job_id)
        logger.info(f"status: {status}")
        if status in waited_status:
            job_status = status
            break
        t.sleep(5)
    job_logs = ray_client.get_job_logs(ray_job_id)
    return job_status, job_logs

def ray_job_handler(
    logger: any,
    allas_client: any,
    allas_bucket: any,
    ray_client: any,
    ray_parameters: any,
    ray_job_path: str,
    ray_job_envs: any,
    timeout: int
) -> bool:
    logger.info('Setting up ray job')

    ray_job_file, ray_job_directory = get_ray_job(
        logger = logger,
        allas_client = allas_client,
        allas_bucket = allas_bucket,
        ray_job_path = ray_job_path
    )

    logger.info('Submitting a ray job')
    ray_job_id = submit_ray_job(
        logger = logger,
        ray_client = ray_client,
        ray_parameters = ray_parameters,
        job_file = ray_job_file,
        working_directory = ray_job_directory,
        job_envs = ray_job_envs
    )

    logger.info('Ray batch job id: ' + str(ray_job_id))
    
    ray_job_status, ray_job_logs = wait_ray_job(
        logger = logger,
        ray_client = ray_client,
        ray_job_id = ray_job_id,
        waited_status = {
            JobStatus.SUCCEEDED, 
            JobStatus.STOPPED, 
            JobStatus.FAILED
        }, 
        timeout = timeout
    )
    logger.info('Ray batch job ended:')
    success = True
    if not ray_job_status == JobStatus.SUCCEEDED:
        logger.info('RAY batch job failed')
        success = False
    else:
        logger.info('RAY batch job succeeded')
    logger.info(ray_job_logs)
    return success


