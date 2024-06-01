import time

from functions.management.objects import get_objects, set_objects
from functions.management.storage import store_bridge_time_templates, store_action_time
# Refactored
def start_job(
    file_lock: any,
    logger: any,
    allas_client: any,
    allas_bucket: str,
    kubeflow_user:str,
    submit: any
) -> bool:
    time_start = time.time()

    submitters_status = get_objects(
        file_lock = file_lock,
        allas_client = allas_client,
        allas_bucket = allas_bucket,
        object = 'submitters-status',
        replacers = {}
    )
    stored = False
    
    if not submitters_status is None:
        user_jobs = submitters_status[kubeflow_user]
        current_key = str(len(user_jobs))
        current_job = user_jobs[current_key]
        job_start = current_job['job-start']
        
        if not job_start:
            store_bridge_time_templates(
                file_lock = file_lock,
                allas_client = allas_client,
                allas_bucket = allas_bucket,
                kubeflow_user = kubeflow_user
            )

            current_job['job-start'] = True
            
            current_job['job-name'] = submit['job-name']

            submit_venv_name = submit['job-enviroment']['venv']['name']
            submit_venv_packages = submit['job-enviroment']['venv']['packages']
            
            if 5 < len(submit_venv_name):
                current_job['job-enviroment']['venv']['name'] = submit['job-enviroment']['venv']['name']
                
            if 0 < len(submit_venv_packages):
                current_job['job-enviroment']['venv']['packages'] = submit['job-enviroment']['venv']['packages']
            
            submit_key_name = submit['job-key']
            if 5 < len(submit_key_name):
                current_job['job-key'] = submit_key_name
            
            submitters_status[kubeflow_user][current_key] = current_job

            set_objects(
                file_lock = file_lock,
                allas_client = allas_client,
                allas_bucket = allas_bucket,
                object = 'submitters-status',
                replacers = {},
                overwrite = True,
                object_data = submitters_status
            )
            logger.info('Job sent by ' + str(kubeflow_user) + ' has been started')
            stored = True

    store_action_time(
        file_lock = file_lock,
        allas_client = allas_client,
        allas_bucket = allas_bucket,
        metadata = {
            'type': 'TIMES',
            'area': 'jobs',
            'user': kubeflow_user
        },
        time_start = time_start,
        action_name = 'start-job'
    )

    return {'submitted':stored}
# Refactored
def stop_job(
    file_lock: any,
    logger: any,
    allas_client: any,
    allas_bucket: str,
    kubeflow_user:str
) -> bool:
    time_start = time.time()

    submitters_status = get_objects(
        file_lock = file_lock,
        allas_client = allas_client,
        allas_bucket = allas_bucket,
        object = 'submitters-status',
        replacers = {}
    )
    stored = False
    if not submitters_status is None:
        user_jobs = submitters_status[kubeflow_user]
        current_key = str(len(user_jobs))
        current_job = user_jobs[current_key]
        job_submit = current_job['job-submit']
        if job_submit:
            current_job['job-cancel'] = True
            submitters_status[kubeflow_user][current_key] = current_job
            set_objects(
                file_lock = file_lock,
                allas_client = allas_client,
                allas_bucket = allas_bucket,
                object = 'submitters-status',
                replacers = {},
                overwrite = True,
                object_data = submitters_status
            )
            logger.info('Job started by ' + str(kubeflow_user) + ' has been cancelled')
            stored = True

    store_action_time(
        file_lock = file_lock,
        allas_client = allas_client,
        allas_bucket = allas_bucket,
        metadata = {
            'type': 'TIMES',
            'area': 'jobs',
            'user': kubeflow_user
        },
        time_start = time_start,
        action_name = 'stop-job'
    )

    return {'cancelled':stored}