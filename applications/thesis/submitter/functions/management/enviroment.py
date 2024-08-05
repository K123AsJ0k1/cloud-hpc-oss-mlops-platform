import os
import time

#from decouple import Config,RepositoryEnv

from functions.general import get_docker_compose_secrets

from functions.platforms.venv import check_python_version, check_venv, check_venv_packages, create_venv, install_packages
from functions.platforms.ssh import upload_file, remote_folders_and_files, run_remote_commands

from functions.management.objects import get_objects
from functions.management.storage import store_action_time

# Refactored
def check_job_enviroment(
    file_lock: any,
    logger: any,
    allas_client: any,
    allas_bucket: str,
    kubeflow_user: str,
    target: str,
    enviroment: any
) -> bool:
    time_start = time.time()
    setup = True
    venv_name = enviroment['venv']['name']
    venv_packages = enviroment['venv']['packages']
    
    if 0 < len(venv_name):
        version = check_python_version(
            logger = logger,
            target = target
        )
        
        if version is None:
            logger.warning('Remote enviroment does not have python')
            setup = False
        
        logger.info('Remote enviroment has python ' + version)
        
        venv_exists = check_venv(
            logger = logger,
            target = target,
            name = venv_name
        )
    
        if venv_exists:
            logger.info(venv_name + ' exists')
            if 0 < len(venv_packages):
                logger.info('Checking packages')
                setup = check_venv_packages(
                    logger = logger,
                    target = target,
                    name = venv_name,
                    wanted_packages = venv_packages
                )

                if setup:
                    logger.info(venv_name + ' has the necessery packages')
        else:
            logger.info(venv_name + ' does not exists')
            setup = False

    logger.info('Enviroment was setup: ' + str(setup))

    store_action_time(
        file_lock = file_lock,
        allas_client = allas_client,
        allas_bucket = allas_bucket,
        metadata = {
            'type': 'TIMES',
            'area': 'bridge',
            'user': kubeflow_user
        },
        time_start = time_start,
        action_name = 'check-job-enviroment'
    )

    return setup
# Refactored
def setup_job_enviroment(
    file_lock: any,
    logger: any,
    allas_client: any,
    allas_bucket: str,
    kubeflow_user: str,
    target: str,
    enviroment: any
) -> bool:
    time_start = time.time()
    
    venv_name = enviroment['venv']['name']
    venv_packages = enviroment['venv']['packages']
    setup_success = True
    if 0 < len(venv_name):
        venv_exists = check_venv(
            logger = logger,
            target = target,
            name = venv_name
        )
        venv_ready = True
        if not venv_exists:
            logger.info('Creating ' + venv_name)
            venv_created = create_venv(
                logger = logger,
                target = target,
                name = venv_name
            )
            
            if not venv_created:
                logger.error(venv_name + ' creation failed')
                venv_ready = False
                setup_success = False

        if venv_ready and 0 < len(venv_packages):
            required_packages = True
            logger.info('Checking packages of ' + venv_name)
            required_packages = check_venv_packages(
                logger = logger,
                target = target,
                name = venv_name,
                wanted_packages = venv_packages
            )
        
            if not required_packages:
                logger.info('Installing wanted packages into ' + venv_name)
                packages_installed = install_packages(
                    logger = logger,
                    target = target,
                    name = venv_name,
                    packages = venv_packages
                )
            
                if packages_installed:
                    logger.info('Wanted packages installed into ' + venv_name)
                else:
                    logger.info('Wanted packages were already installed in ' + venv_name)
    
    store_action_time(
        file_lock = file_lock,
        allas_client = allas_client,
        allas_bucket = allas_bucket,
        metadata = {
            'type': 'TIMES',
            'area': 'bridge',
            'user': kubeflow_user
        },
        time_start = time_start,
        action_name = 'setup-job-enviroment'
    )

    return setup_success
# Created and works
def check_remote_file(
    file_lock: any,
    logger: any,
    allas_client: any,
    allas_bucket: str,
    kubeflow_user: str,
    target: str,
    file_name: any
) -> bool:
    time_start = time.time()
    
    _ ,files = remote_folders_and_files(
        logger = logger,
        target = target
    )
    
    found = False
    if file_name in files:
        logger.info(file_name + ' was found in remote enviroment')
        found = True
    else:
        logger.info(file_name + ' was not found in remote enviroment')

    store_action_time(
        file_lock = file_lock,
        allas_client = allas_client,
        allas_bucket = allas_bucket,
        metadata = {
            'type': 'TIMES',
            'area': 'bridge',
            'user': kubeflow_user
        },
        time_start = time_start,
        action_name = 'check-remote-file'
    )

    return found
# Created and works
def send_job_key(
    file_lock: any,
    logger: any,
    allas_client: any,
    allas_bucket: str,
    kubeflow_user: str,
    target: str,
    file_name: any
) -> bool:
    time_start = time.time()

    #env_config = Config(RepositoryEnv('.env'))
    #used_key_filename = env_config.get('BRIDGE_PRIVATE_KEY_PATH')

    secrets = get_docker_compose_secrets()
    used_key_filename = secrets['BRIDGE_PRIVATE_KEY_PATH']
    
    local_key_path = os.path.expanduser(used_key_filename)
    if not os.path.exists(local_key_path):
        logger.warning(file_name + ' does not exists in the designated folder')
        return False
    logger.info(file_name + ' exists in the designated folder')

    upload_file(
        logger = logger,
        target = target,
        given_local_path = local_key_path,
        remote_file_name = file_name
    )
    logger.info(file_name + ' sending to remote target succeeded')

    file_permission_command = 'chmod 600 ' + file_name
    run_remote_commands(
        logger = logger,
        target = target,
        commands = [
            file_permission_command
        ]
    )
    logger.info(file_name + ' in remote enviroment was given chmod 600')

    store_action_time(
        file_lock = file_lock,
        allas_client = allas_client,
        allas_bucket = allas_bucket,
        metadata = {
            'type': 'TIMES',
            'area': 'bridge',
            'user': kubeflow_user
        },
        time_start = time_start,
        action_name = 'send-job-key'
    )

    return True
# Created and works
def send_job_file(
    file_lock: any,
    logger: any,
    allas_client: any,
    allas_bucket: str,
    kubeflow_user: str,
    target: str,
    file_name: str
) -> bool:
    time_start = time.time()
    
    jobs_folder = 'jobs'
    os.makedirs(jobs_folder, exist_ok=True)
    file_path = os.path.expanduser(jobs_folder + '/' + file_name)
    job_name = file_name.split('.')[0]
    job_data = get_objects(
        file_lock = file_lock,
        allas_client = allas_client,
        allas_bucket = allas_bucket,
        object = 'slurm-job',
        replacers = {
            'username': kubeflow_user,
            'name': job_name
        }
    )
    
    if job_data is None:
        logger.error(file_name + ' is either incorrect or the file does not exist')
        return False
    
    with open(file_path, 'w') as f:
        f.write(job_data)
    
    upload_file(
        logger = logger,
        target = target,
        given_local_path = file_path,
        remote_file_name = file_name
    )
    logger.info(file_name + ' was sent to remote enviroment')
    
    store_action_time(
        file_lock = file_lock,
        allas_client = allas_client,
        allas_bucket = allas_bucket,
        metadata = {
            'type': 'TIMES',
            'area': 'bridge',
            'user': kubeflow_user
        },
        time_start = time_start,
        action_name = 'send-job-file'
    )

    return True