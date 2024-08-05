import time

from functions.management.objects import get_objects, set_objects
from functions.management.enviroment import check_job_enviroment, setup_job_enviroment, check_remote_file, send_job_key, send_job_file
from functions.management.storage import store_action_time
# Refactored and works
def configure_remote_enviroment(
    file_lock: any,
    logger: any,
    allas_client: any,
    allas_bucket: str,
    kubeflow_user: str,
    target: str,
    job_enviroment: any,
    key_name: str,
    job_name: str
) -> bool:
    time_start = time.time()
    
    success = True
    enviroment_ready = check_job_enviroment(
        file_lock = file_lock,
        logger = logger,
        allas_client = allas_client,
        allas_bucket = allas_bucket,
        kubeflow_user = kubeflow_user,
        target = target,
        enviroment = job_enviroment
    )
    
    if not enviroment_ready:
        logger.info('Configuring enviroment')
        # Might require specific package installation
        enviroment_setup = setup_job_enviroment(
            file_lock = file_lock,
            logger = logger,
            allas_client = allas_client,
            allas_bucket = allas_bucket,
            kubeflow_user = kubeflow_user,
            target = target,
            enviroment = job_enviroment
        )
        
        if not enviroment_setup:
            logger.error('Enviroment configuration failed')
            success = False
        else:
            logger.info('Enviroment configuration success')

    if 0 < len(key_name):  
        key_file = key_name + '.pem'
        key_ready = check_remote_file(
            file_lock = file_lock,
            logger = logger,
            allas_client = allas_client,
            allas_bucket = allas_bucket,
            kubeflow_user = kubeflow_user,
            target = target,
            file_name = key_file
        )

        if not key_ready:
            logger.info('Sending key')

            key_sent = send_job_key(
                file_lock = file_lock,
                logger = logger,
                allas_client = allas_client,
                allas_bucket = allas_bucket,
                kubeflow_user = kubeflow_user,
                target = target,
                file_name = key_file
            )

            if not key_sent:
                logger.error('Key sending failed')
                success = False
            else:
                logger.info('Key sending success')

    logger.info('Sending job')

    job_file = job_name + '.sh'
    job_sent = send_job_file(
        file_lock = file_lock,
        logger = logger,
        allas_client = allas_client,
        allas_bucket = allas_bucket,
        kubeflow_user = kubeflow_user,
        target = target,
        file_name = job_file
    )

    if not job_sent:
        logger.error('Job sending failed') 
        success = False
    else:
        logger.info('Job sending success')

    store_action_time(
        file_lock = file_lock,
        allas_client = allas_client,
        allas_bucket = allas_bucket,
        metadata = {
            'type': 'TIMES',
            'area': 'setup',
            'user': kubeflow_user
        },
        time_start = time_start,
        action_name = 'configure-remote-enviroment'
    ) 

    return success
# Created and works
def check_and_setup_remote(
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
        logger.warning('Status was none')
        return False

    if not kubeflow_user in submitters_status:
        logger.warning('The user was not in status')
        return False
    
    jobs = submitters_status[kubeflow_user]
    current_job = jobs[str(len(jobs))]
    
    job_start = current_job['job-start']
    #job_cancel = current_job['job-cancel']
    job_ready = current_job['job-ready']
    
    job_enviroment = current_job['job-enviroment']
    job_key_name = current_job['job-key']
    job_name = current_job['job-name']

    if not job_start:
        logger.warning('Job was not initilized')
        return False
    
    #if job_cancel:
    #    logger.info('Job was already cancelled')
    #    return False
    
    if job_ready:
        logger.info('Job was already checked')
        return False

    configuration_success = configure_remote_enviroment(
        file_lock = file_lock,
        logger = logger,
        allas_client = allas_client,
        allas_bucket = allas_bucket,
        kubeflow_user = kubeflow_user,
        target = target,
        job_enviroment = job_enviroment,
        key_name = job_key_name,
        job_name = job_name
    )
    
    logger.info('Remote enviroment is configured')

    if configuration_success:
        submitters_status[kubeflow_user][str(len(jobs))]['job-ready'] = True
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
            'area': 'setup',
            'user': kubeflow_user
        },
        time_start = time_start,
        action_name = 'check-and-setup'
    ) 

    return True

    