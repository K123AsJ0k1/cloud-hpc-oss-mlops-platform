
import time
#from decouple import Config,RepositoryEnv

from functions.initilization import job_status_template
from functions.platforms.ssh import run_remote_commands
from functions.management.objects import get_objects, set_objects
from functions.management.storage import store_action_time
from functions.platforms.slurm import save_slurm_squeue, parse_slurm_squeue
from functions.general import get_docker_compose_secrets

# Created and works
def check_job(
    file_lock: any,
    logger: any,
    allas_client: any,
    allas_bucket: str,
    kubeflow_user: str,
    target: str,
    job_id: str
):
    time_start = time.time()

    state_codes = {
        'BF': 'BOOT FAIL',
        'CA': 'CANCELLED',
        'CD': 'COMPLETED',
        'CF': 'CONFIGURING',
        'CG': 'COMPLETING',
        'DL': 'DEADLINE',
        'F': 'FAILED',
        'NF': 'NODE FAIL',
        'OOM': 'OUT OF MEMORY',
        'PD': 'PENDING',
        'PR': 'PREEMPTED',
        'R': 'RUNNING',
        'RD': 'RESERVATION DELETION HOLD',
        'RF': 'REQUEUE FEDERATION',
        'RH': 'REQUEUE HOLD',
        'RQ': 'REQUEUED',
        'RS': 'RESIZING',
        'RV': 'REVOKED',
        'SI': 'SIGNALING',
        'SE': 'SPECIAL EXIT',
        'SO': 'STAGE OUT',
        'ST': 'STOPPED',
        'S': 'SUSPENDED',
        'TO': 'TIMEOUT'
    }

    #env_config = Config(RepositoryEnv('.env'))
    #used_user = env_config.get('CSC_USER')

    secrets = get_docker_compose_secrets()
    used_user = secrets['CSC_USER']
    
    save_slurm_squeue(
        logger = logger,
        target = target,
        csc_user = used_user
    )

    job_pending = False
    pending_states = [
        'PENDING',
        'CONFIGURING',
        'REQUEUE FEDERATION',
        'REQUEUE HOLD',
        'REQUEUED',
        'RESIZING',
        'STAGE OUT'
    ]

    job_running = False
    running_states = [
        'RUNNING',
        'SIGNALING'
    ]

    job_failure = False
    failure_states = [
        'BOOT FAIL',
        'OUT OF MEMORY',
        'NODE FAIL',
        'REVOKED'
    ]
    
    job_completion = False
    completion_states = [
        'COMPLETED',
        'DEADLINE',
        'CANCELLED',
        'COMPLETING',
        'TIMEOUT',
        'SPECIAL EXIT',
        'PREEMPTED',
        'RESERVATION DELETION HOLD',
        'STOPPED',
        'SUSPENDED'
    ]
    
    squeue_dict = parse_slurm_squeue()
    if 0 < len(squeue_dict):
        logger.info('Current ' + str(target) + ' squeue:')
        for key in squeue_dict.keys():
            id = squeue_dict[key]['JOBID']
            state = state_codes[squeue_dict[key]['ST']]
            user = squeue_dict[key]['USER']
            elapsed = squeue_dict[key]['TIME']
            partition = squeue_dict[key]['PARTITION']
            logger.info(str(user) + ' ' + str(id) + ' ' + str(partition) + ' ' + str(state) + ' ' + str(elapsed))
            if job_id == id:
                if state in pending_states:
                    job_pending = True
                if state in running_states:
                    job_running = True
                if state in failure_states:
                    job_failure = True
                if state in completion_states:
                    job_completion = True   
            else:
                job_completion = True
    else:
        logger.info('No jobs running under ' + str(used_user) + ' in ' + str(target))
    
    job_states = [
        job_pending, 
        job_running, 
        job_failure, 
        job_completion
    ]

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
        action_name = 'check-job'
    ) 

    return job_states
# Created and works
def cancel_job(
    logger: any,
    target: str,
    job_id: str
):
    scancel_command = 'scancel ' + job_id
    results = run_remote_commands(
        logger = logger,
        target = target,
        commands = [
            scancel_command
        ]
    )
    if len(results[0]) == 0:
        return True
    return False
# Created and works
def halt_job(
    file_lock: any,
    logger: any,
    allas_client: any,
    allas_bucket: str,
    kubeflow_user: str,
    target: str,
    job_id: str
) -> bool:
    time_start = time.time()
    
    job_canceled = cancel_job(
        logger = logger,
        target = target,
        job_id = job_id
    )

    if not job_canceled:
        logger.info('Job was not found or running')
        return False 

    store_action_time(
        file_lock = file_lock,
        allas_client = allas_client,
        allas_bucket = allas_bucket,
        metadata = {
            'type': 'TIMES',
            'area': 'cancel',
            'user': kubeflow_user
        },
        time_start = time_start,
        action_name = 'halt-job'
    )
    
    return True
# Refactor
def complete_job(
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
        current_key = str(len(jobs))
        current_job = jobs[current_key]
        job_id = current_job['job-id']
        job_submit = current_job['job-submit']
        job_cancel = current_job['job-cancel']
        job_name = current_job['job-name']

        if job_id.isnumeric() and job_submit:
            job_states = check_job(
                file_lock = file_lock,
                logger = logger,
                allas_client = allas_client,
                allas_bucket = allas_bucket,
                kubeflow_user = kubeflow_user,
                target = target,
                job_id = job_id
            )
            
            complete_job = False
            if job_states[0]:
                current_job['job-pending'] = True
            
            if job_states[1]:
                current_job['job-running'] = True

            if job_states[2]:
                current_job['job-failed'] = True

            if job_states[3]:
                complete_job = True
                current_job['job-complete'] = True
                logger.info('Job ' + str(job_name) + ' of ' + str(job_id) + ' was already completed')
            else:
                if job_cancel or job_states[2]:
                    job_stopped = halt_job(
                        file_lock = file_lock,
                        logger = logger,
                        allas_client = allas_client,
                        allas_bucket = allas_bucket,
                        kubeflow_user = kubeflow_user,
                        target = target,
                        job_id = job_id
                    )
                    if job_stopped:
                        logger.info('Job ' + str(job_name) + ' of ' + str(job_id) + ' was stopped')
                    else:
                        logger.info('Job ' + str(job_name) + ' of ' + str(job_id) + ' was not stopped')
                        current_job['job-failed'] = True
                    current_job['job-complete'] = True
                    complete_job = True
                    
            if complete_job:
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

                job_start = job_times[kubeflow_user][highest_time_key]['start-time']
                job_end = time.time()
                job_total_time = (job_end-job_start)
                
                job_times[kubeflow_user][highest_time_key]['end-time'] = job_end
                job_times[kubeflow_user][highest_time_key]['total-seconds'] = job_total_time

                next_key = str(len(jobs) + 1)
                submitters_status[kubeflow_user][next_key] = job_status_template()

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

                gather_times[kubeflow_user][highest_gather_key]['start-time'] = time.time()
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
        
    store_action_time(
        file_lock = file_lock,
        allas_client = allas_client,
        allas_bucket = allas_bucket,
        metadata = {
            'type': 'TIMES',
            'area': 'cancel',
            'user': kubeflow_user
        },
        time_start = time_start,
        action_name = 'complete-job'
    ) 