import time

from functions.platforms.slurm import save_slurm_seff, save_slurm_log, save_slurm_sacct, parse_slurm_seff, parse_slurm_logs, parse_slurm_sacct
from functions.management.storage import store_action_time
from functions.management.objects import get_objects, set_objects
# Refactored and works
def store_seff(
    file_lock: any,
    logger: any,
    allas_client: any,
    allas_bucket: str,
    kubeflow_user: str,
    target: str,
    job_id: str
): 
    time_start = time.time()

    current_data = get_objects(
        file_lock = file_lock,
        allas_client = allas_client,
        allas_bucket = allas_bucket,
        object = 'user-object',
        replacers = {
            'purpose': 'MONITOR',
            'username': kubeflow_user,
            'object': 'seff'
        }
    )

    object_data = None
    if current_data is None:
        object_data = {}
    else:
        object_data = current_data

    logger.info('Getting job ' + str(job_id) + ' seff')

    save_slurm_seff(
        logger = logger,
        target = target,
        job_id = job_id
    )

    seff_dict = parse_slurm_seff(
        job_id = job_id
    )

    new_key = len(object_data) + 1
    object_data[str(new_key)] = seff_dict

    set_objects(
        file_lock = file_lock,
        allas_client = allas_client,
        allas_bucket = allas_bucket,
        object = 'user-object',
        replacers = {
            'purpose': 'MONITOR',
            'username': kubeflow_user,
            'object': 'seff'
        },
        overwrite = True,
        object_data = object_data
    )

    logger.info('Job ' + str(job_id) + ' seff stored')

    store_action_time(
        file_lock = file_lock,
        allas_client = allas_client,
        allas_bucket = allas_bucket,
        metadata = {
            'type': 'TIMES',
            'area': 'monitor',
            'user': kubeflow_user
        },
        time_start = time_start,
        action_name = 'store-seff'
    ) 
# Refactored and works
def store_sacct(
    file_lock: any,
    logger: any,
    allas_client: any,
    allas_bucket: str,
    kubeflow_user: str,
    target: str,
    job_id: str 
):
    time_start = time.time()

    current_data = get_objects(
        file_lock = file_lock,
        allas_client = allas_client,
        allas_bucket = allas_bucket,
        object = 'user-object',
        replacers = {
            'purpose': 'MONITOR',
            'username': kubeflow_user,
            'object': 'sacct'
        }
    )

    object_data = None
    if current_data is None:
        object_data = {}
    else:
        object_data = current_data

    logger.info('Getting job ' + str(job_id) + ' sacct')

    save_slurm_sacct(
        logger = logger,
        target = target,
        job_id = job_id
    )

    sacct_dict = parse_slurm_sacct(
        job_id = job_id
    )

    new_key = len(object_data) + 1
    object_data[str(new_key)] = sacct_dict

    set_objects(
        file_lock = file_lock,
        allas_client = allas_client,
        allas_bucket = allas_bucket,
        object = 'user-object',
        replacers = {
            'purpose': 'MONITOR',
            'username': kubeflow_user,
            'object': 'sacct'
        },
        overwrite = True,
        object_data = object_data
    )
    logger.info('Job ' + str(job_id) + ' sacct stored')

    store_action_time(
        file_lock = file_lock,
        allas_client = allas_client,
        allas_bucket = allas_bucket,
        metadata = {
            'type': 'TIMES',
            'area': 'monitor',
            'user': kubeflow_user
        },
        time_start = time_start,
        action_name = 'store-sacct'
    ) 
# Created and works
def store_logs(
    file_lock: any,
    logger: any,
    allas_client: any,
    allas_bucket: str,
    kubeflow_user: str,
    target: str,
    job_id: str 
):
    time_start = time.time()

    logger.info('Getting job ' + str(job_id) + ' logs')

    save_slurm_log(
        logger = logger,
        target = target,
        job_id = job_id
    )

    log_list = parse_slurm_logs(
        job_id = job_id
    )

    set_objects(
        file_lock = file_lock,
        allas_client = allas_client,
        allas_bucket = allas_bucket,
        object = 'user-object',
        replacers = {
            'purpose': 'LOGS',
            'username': kubeflow_user,
            'object': job_id
        },
        overwrite = True,
        object_data = log_list
    )

    logger.info('Job ' + str(job_id) + ' logs stored')

    store_action_time(
        file_lock = file_lock,
        allas_client = allas_client,
        allas_bucket = allas_bucket,
        metadata = {
            'type': 'TIMES',
            'area': 'monitor',
            'user': kubeflow_user
        },
        time_start = time_start,
        action_name = 'store-logs'
    ) 
# Created and works
def store_metrics(
    file_lock: any,
    logger: any,
    allas_client: any,
    allas_bucket: str,
    kubeflow_user: str,
    target: str,
    job_id: str
):
    time_start = time.time()

    store_seff(
        file_lock = file_lock,
        logger = logger,
        allas_client = allas_client,
        allas_bucket = allas_bucket,
        kubeflow_user = kubeflow_user,
        target = target,
        job_id = job_id
    )
    
    time.sleep(5)
    
    store_logs(
        file_lock = file_lock,
        logger = logger,
        allas_client = allas_client,
        allas_bucket = allas_bucket,
        kubeflow_user = kubeflow_user,
        target = target,
        job_id = job_id
    )

    time.sleep(10)
    
    store_sacct(
        file_lock = file_lock,
        logger = logger,
        allas_client = allas_client,
        allas_bucket = allas_bucket,
        kubeflow_user = kubeflow_user,
        target = target,
        job_id = job_id
    )

    store_action_time(
        file_lock = file_lock,
        allas_client = allas_client,
        allas_bucket = allas_bucket,
        metadata = {
            'type': 'TIMES',
            'area': 'monitor',
            'user': kubeflow_user
        },
        time_start = time_start,
        action_name = 'store-metrics'
    ) 
    
    logger.info('Job ' + str(job_id) + ' metrics stored')
# Created and works
def gather_metrics(
    file_lock: any,
    logger: any,
    allas_client: any,
    allas_bucket: str,
    target: str,
    kubeflow_user: str
):
    time_start = time.time()

    submitters_status = get_objects(
        file_lock = file_lock,
        allas_client = allas_client,
        allas_bucket = allas_bucket,
        object = 'submitters-status',
        replacers = {}
    )

    if not submitters_status is None:
        jobs = submitters_status[kubeflow_user]
        target_job = None
        target_job_key = None
        for key in jobs.keys():
            job_complete = jobs[key]['job-complete'] 
            job_stored = jobs[key]['job-stored']
            if job_complete and not job_stored:
                target_job_key = key
                target_job = jobs[key]  
                break

        if not target_job is None:
            job_name = target_job['job-name']
            job_id = target_job['job-id']
            
            gather_times = get_objects(
                file_lock = file_lock,
                allas_client = allas_client,
                allas_bucket = allas_bucket,
                object = 'bridge-object',
                replacers = {
                    'purpose': 'TIMES',
                    'object': 'gather'
                }
            )
            highest_gather_key = str(len(gather_times[kubeflow_user]))

            gather_start = gather_times[kubeflow_user][highest_gather_key]['start-time']
            gather_end = time.time()
            gather_total = round((gather_end-gather_start),3)
            logger.info('Gathering job ' + str(job_name) + ' of ' + str(job_id) + ' metrics with wait time of ' + str(gather_total))
            
            if 120 < gather_total:
                store_metrics(
                    file_lock = file_lock,
                    logger = logger,
                    allas_client = allas_client,
                    allas_bucket = allas_bucket,
                    kubeflow_user = kubeflow_user,
                    target = target,
                    job_id = job_id
                ) 

                target_job['job-stored'] = True             

                gather_times[kubeflow_user][highest_gather_key]['end-time'] = gather_end
                gather_times[kubeflow_user][highest_gather_key]['total-seconds'] = gather_total

                pipeline_times = get_objects(
                    file_lock = file_lock,
                    allas_client = allas_client,
                    allas_bucket = allas_bucket,
                    object = 'bridge-object',
                    replacers = {
                        'purpose': 'TIMES',
                        'object': 'pipeline'
                    }
                )
                highest_pipeline_key = str(len(pipeline_times[kubeflow_user]))

                pipeline_start = pipeline_times[kubeflow_user][highest_pipeline_key]['start-time']
                pipeline_end = time.time()
                pipeline_total = (pipeline_end-pipeline_start)
                
                pipeline_times[kubeflow_user][highest_pipeline_key]['end-time'] = pipeline_end 
                pipeline_times[kubeflow_user][highest_pipeline_key]['total-seconds'] = pipeline_total

                submitters_status[kubeflow_user][str(target_job_key)] = target_job

                set_objects(
                    file_lock = file_lock,
                    allas_client = allas_client,
                    allas_bucket = allas_bucket,
                    object = 'submitters-status',
                    replacers = {},
                    overwrite = True,
                    object_data = submitters_status
                )

                set_objects(
                    file_lock = file_lock,
                    allas_client = allas_client,
                    allas_bucket = allas_bucket,
                    object = 'bridge-object',
                    replacers = {
                        'purpose': 'TIMES',
                        'object': 'gather'
                    },
                    overwrite = True,
                    object_data = gather_times
                )

                set_objects(
                    file_lock = file_lock,
                    allas_client = allas_client,
                    allas_bucket = allas_bucket,
                    object = 'bridge-object',
                    replacers = {
                        'purpose': 'TIMES',
                        'object': 'pipeline'
                    },
                    overwrite = True,
                    object_data = pipeline_times
                )

                logger.info('Job ' + str(job_name) + ' of ' + str(job_id) + ' metrics gathered')

    store_action_time(
        file_lock = file_lock,
        allas_client = allas_client,
        allas_bucket = allas_bucket,
        metadata = {
            'type': 'TIMES',
            'area': 'monitor',
            'user': kubeflow_user
        },
        time_start = time_start,
        action_name = 'gather-metrics'
    ) 