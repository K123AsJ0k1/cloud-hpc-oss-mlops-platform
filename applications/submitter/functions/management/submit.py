import time

from functions.platforms.ssh import run_remote_commands
from functions.management.objects import get_objects, set_objects
from functions.management.storage import store_action_time

# Created and works
def submit_job(
    logger: any,
    target: str,
    job_name: str
) -> bool:
    file_name = job_name + '.sh'
    # Here source /appl/profile/zz-csc-env.sh ensures module loading
    sbatch_command = 'source /appl/profile/zz-csc-env.sh && sbatch ' + file_name
    results = run_remote_commands(
        logger = logger,
        target = target,
        commands = [
            sbatch_command
        ]
    )
    job_id = results[0].split(' ')[-1]
    job_id = job_id.replace('\n','')
    return job_id
# Created and works
def run_job(
    file_lock: any,
    logger: any,
    allas_client: any,
    allas_bucket: str,
    target: str,
    kubeflow_user: str
) -> bool:
    time_start = time.time()

    submitters_status = get_objects(
        file_lock = file_lock,
        allas_client = allas_client,
        allas_bucket = allas_bucket,
        object = 'submitters-status',
        replacers = {}
    )

    if submitters_status is None:
        logger.info('Status was none') 
        return False

    jobs = submitters_status[kubeflow_user]
    current_job = jobs[str(len(jobs))]
    
    job_ready = current_job['job-ready']

    job_name = current_job['job-name']

    if not job_ready:
        logger.info('Job was not READY') 
        return False

    job_times = get_objects(
        file_lock = file_lock,
        allas_client = allas_client,
        allas_bucket = allas_bucket,
        object = 'bridge-object',
        replacers = {
            'purpose': 'TIMES',
            'object': 'job'
        }
    )

    highest_time_key = str(len(job_times[kubeflow_user]))
    job_times[kubeflow_user][highest_time_key]['start-time'] = time.time()
    
    job_id = submit_job(
        logger = logger,
        target = target,
        job_name = job_name
    )
    logger.info('Job ' + str(job_id) + ' is now submitted')
    
    current_job['job-submit'] = True
    current_job['job-id'] = job_id 
    submitters_status[kubeflow_user][str(len(jobs))] = current_job
 
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
            'object': 'job'
        },
        overwrite = True,
        object_data = job_times
    )

    store_action_time(
        file_lock = file_lock,
        allas_client = allas_client,
        allas_bucket = allas_bucket,
        metadata = {
            'type': 'TIMES',
            'area': 'submit',
            'user': kubeflow_user
        },
        time_start = time_start,
        action_name = 'run-job'
    ) 

    return True