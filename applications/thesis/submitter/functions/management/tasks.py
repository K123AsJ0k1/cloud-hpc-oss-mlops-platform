import time

from functions.management.setup import check_and_setup_remote
from functions.management.storage import store_action_time
from functions.management.submit import run_job
from functions.management.cancel import complete_job
from functions.management.monitor import gather_metrics
# Created and works
def submitter(
    task_file_lock: any,
    task_logger: any,
    task_allas_client: any,
    task_allas_bucket: str,
    task_target: any,
    task_kubeflow_user: str
):
    time_start = time.time()

    task_logger.info('Running submitter') 

    remote_ready = check_and_setup_remote(
        file_lock = task_file_lock,
        logger = task_logger,
        allas_client = task_allas_client,
        allas_bucket = task_allas_bucket,
        target = task_target,
        kubeflow_user = task_kubeflow_user
    )

    if remote_ready:
        job_running = run_job(
            file_lock = task_file_lock,
            logger = task_logger,
            allas_client = task_allas_client,
            allas_bucket = task_allas_bucket,
            target = task_target,
            kubeflow_user = task_kubeflow_user
        )
        task_logger.info('Job was made to run: ' + str(job_running))

    store_action_time(
        file_lock = task_file_lock,
        allas_client = task_allas_client,
        allas_bucket = task_allas_bucket,
        metadata = {
            'type': 'TIMES',
            'area': 'task',
            'user': task_kubeflow_user
        },
        time_start = time_start,
        action_name = 'submitter'
    ) 
# Created and works
def monitor(
    task_file_lock: any,
    task_logger: any,
    task_allas_client: any,
    task_allas_bucket: str,
    task_target: any,
    task_kubeflow_user: str
):
    time_start = time.time()

    task_logger.info('Running monitor')

    complete_job(
        file_lock = task_file_lock,
        logger = task_logger,
        allas_client = task_allas_client,
        allas_bucket = task_allas_bucket,
        target = task_target,
        kubeflow_user = task_kubeflow_user
    )

    gather_metrics(
        file_lock = task_file_lock,
        logger = task_logger,
        allas_client = task_allas_client,
        allas_bucket = task_allas_bucket,
        target = task_target,
        kubeflow_user = task_kubeflow_user
    )

    store_action_time(
        file_lock = task_file_lock,
        allas_client = task_allas_client,
        allas_bucket = task_allas_bucket,
        metadata = {
            'type': 'TIMES',
            'area': 'task',
            'user': task_kubeflow_user
        },
        time_start = time_start,
        action_name = 'monitor'
    ) 