import time

from functions.management.bridges import bridge_scaler
from functions.management.storage import store_action_time
from functions.metrics.sacct import gather_submitter_sacct
from functions.metrics.seff import gather_submitter_seff
from functions.metrics.times import gather_name_times, gather_user_times

# Refactored and works
def scaler( 
    task_file_lock: any,
    task_logger: any,
    task_allas_client: any,
    task_allas_bucket: any   
):
    time_start = time.time()

    task_logger.info('Running scaler')

    bridge_scaler(
        file_lock = task_file_lock,
        logger = task_logger,
        allas_client = task_allas_client,
        allas_bucket = task_allas_bucket
    )

    store_action_time(
        file_lock = task_file_lock,
        allas_client = task_allas_client,
        allas_bucket = task_allas_bucket,
        metadata = {
            'type': 'TIMES',
            'area': 'task'
        },
        time_start = time_start,
        action_name = 'scaler'
    )
# Refactored and works
def monitor(
    task_file_lock: any,
    task_logger: any,
    task_allas_client: any,
    task_allas_bucket: any,
    task_prometheus_registry: any,
    task_prometheus_metrics: any
):
    time_start = time.time()

    task_logger.info('Running monitor')

    gather_name_times(
        file_lock = task_file_lock,
        logger = task_logger,
        prometheus_metrics = task_prometheus_metrics,
        allas_client = task_allas_client,
        allas_bucket = task_allas_bucket
    )

    gather_user_times(
        file_lock = task_file_lock,
        logger = task_logger,
        prometheus_metrics = task_prometheus_metrics,
        allas_client = task_allas_client,
        allas_bucket = task_allas_bucket,
        type = 'SUBMITTER'
    )

    gather_user_times(
        file_lock = task_file_lock,
        logger = task_logger,
        prometheus_metrics = task_prometheus_metrics,
        allas_client = task_allas_client,
        allas_bucket = task_allas_bucket,
        type = 'BRIDGE'
    )

    gather_submitter_seff(
        file_lock = task_file_lock,
        logger = task_logger,
        prometheus_metrics = task_prometheus_metrics,
        allas_client = task_allas_client,
        allas_bucket = task_allas_bucket
    )

    gather_submitter_sacct(
        file_lock = task_file_lock,
        logger = task_logger,
        prometheus_metrics = task_prometheus_metrics,
        allas_client = task_allas_client,
        allas_bucket = task_allas_bucket
    )

    store_action_time(
        file_lock = task_file_lock,
        allas_client = task_allas_client,
        allas_bucket = task_allas_bucket,
        metadata = {
            'type': 'TIMES',
            'area': 'task'
        },
        time_start = time_start,
        action_name = 'monitor'
    )