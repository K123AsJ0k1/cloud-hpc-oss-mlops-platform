import os

#from decouple import Config,RepositoryEnv
from paramiko import RSAKey, Ed25519Key
from fabric import Connection

from functions.general import get_docker_compose_secrets

# Created and works
def get_mahti_connection_parameters() -> any:
    #env_config = Config(RepositoryEnv('.env'))
    #used_host = env_config.get('MAHTI_NODE_ADDRESS')
    #used_user = env_config.get('CSC_USER')
    #used_key_filename = os.path.expanduser(env_config.get('MAHTI_PRIVATE_KEY_PATH'))
    #used_key_passphrase = env_config.get('MAHTI_PRIVATE_KEY_PASSWORD')

    secrets = get_docker_compose_secrets()
    used_host = secrets['MAHTI_NODE_ADDRESS']
    used_user = secrets['CSC_USER']
    used_key_filename = secrets['MAHTI_PRIVATE_KEY_PATH']
    used_key_passphrase = secrets['MAHTI_PRIVATE_KEY_PASSPHRASE']

    private_key = Ed25519Key.from_private_key_file(used_key_filename, password = used_key_passphrase)

    connect_parameters = {
        'host': used_host,
        'user': used_user,
        'kwargs': {
            'pkey': private_key
        }
    }
    return connect_parameters
'''
# Created and works
def get_cpouta_connection_parameters() -> any:
    env_config = Config(RepositoryEnv('.env'))
    used_host = env_config.get('CPOUTA_VM_FIP')
    used_user = env_config.get('CPOUTA_VM_USER')
    used_key_filename = os.path.expanduser(env_config.get('CPOUTA_PRIVATE_KEY_PATH'))
    used_key_passphrase = env_config.get('CPOUTA_PRIVATE_KEY_PASSWORD')

    #secrets = get_docker_compose_secrets()
    #used_host = secrets['CPOUTA_VM_FIP']
    #used_user = secrets['CPOUTA_VM_USER']
    #used_key_filename = secrets['CPOUTA_PRIVATE_KEY_PATH']
    #used_key_passphrase = secrets['CPOUTA_PRIVATE_KEY_PASSPHRASE']

    private_key = RSAKey.from_private_key_file(used_key_filename, password=used_key_passphrase)

    connect_parameters = {
        'host': used_host,
        'user': used_user,
        'kwargs': {
            'pkey': private_key
        }
    }
    return connect_parameters
'''
# Refactored and works
def upload_file(
    logger: any,
    target: str,
    given_local_path: str,
    remote_file_name: str
):  
    logger.info('Uploading a file ' + str(remote_file_name) + ' to ' + str(target))
    connection_parameters = None
    '''
    if target == 'cpouta':
        connection_parameters = get_cpouta_connection_parameters()
    '''
    if target == 'mahti':
        connection_parameters = get_mahti_connection_parameters()
    if connection_parameters:
        with Connection(
            host = connection_parameters['host'],
            user = connection_parameters['user'],
            connect_kwargs = connection_parameters['kwargs']
        ) as c:
            result = c.run('pwd', hide=True)
            starting_directory = ''
            if result.ok:
                starting_directory = result.stdout

            starting_directory = starting_directory.replace('\n','') 
            local_path = os.path.abspath(given_local_path)
            remote_path = starting_directory + '/' + remote_file_name
            c.put(
                local = local_path, 
                remote = remote_path
            )
# Refactored and works
def download_file(
    logger: any,
    target: str,
    given_local_path: str,
    remote_file_name: str
): 
    logger.info('Downloading a file ' + str(remote_file_name) + ' from ' + str(target))
    connection_parameters = None
    '''
    if target == 'cpouta':
        connection_parameters = get_cpouta_connection_parameters()
    '''
    if target == 'mahti':
        connection_parameters = get_mahti_connection_parameters()
    if connection_parameters:
        with Connection(
            host = connection_parameters['host'],
            user = connection_parameters['user'],
            connect_kwargs = connection_parameters['kwargs']
        ) as c:
            result = c.run('pwd', hide=True)
            starting_directory = ''
            if result.ok:
                starting_directory = result.stdout
            starting_directory = starting_directory.replace('\n','')
            local_path = os.path.abspath(given_local_path)
            remote_path = starting_directory + '/' + remote_file_name
            c.get(
                remote = remote_path,
                local = local_path
            )   
# Created and works
def run_remote_commands(
    logger: any,
    target: str,
    commands: any
):
    logger.info('Running remote commands in ' + str(target))
    connection_parameters = None
    '''
    if target == 'cpouta':
        connection_parameters = get_cpouta_connection_parameters()
    '''
    if target == 'mahti':
        connection_parameters = get_mahti_connection_parameters()
    run_results = []
    if connection_parameters:
        with Connection(
            host = connection_parameters['host'],
            user = connection_parameters['user'],
            connect_kwargs = connection_parameters['kwargs']
        ) as c:
            result = c.run('pwd', hide=True)
            starting_directory = ''
            if result.ok:
                starting_directory = result.stdout
        
            for command in commands:
                result = c.run(command, hide=True)
                if result.ok:
                    run_results.append(result.stdout)
    return run_results   
# Created and works
def remote_folders_and_files(
    logger: any,
    target: str
) -> any:
    ls_print = run_remote_commands(
        logger = logger,
        target = target,
        commands = ['ls']
    )
    formatted_names = ls_print[0].split('\n')[:-1]
    folders = []
    files = []
    for name in formatted_names:
        if '.' in name:
            files.append(name)
        else:
            folders.append(name)
    return folders,files   
# Created and works
def remove_folder_or_file(
    logger: any,
    target: str,
    name: str
) -> bool:
    folders, files = remote_folders_and_files(
        logger = logger,
        target = target
    )
    
    target_is_folder = False
    for folder in folders:
        if name == folder:
            target_is_folder = True
            break
    
    target_is_file = False
    for file in files:
        if name == file:
            target_is_file = True
            break

    removal_command = None
    if target_is_folder:
        removal_command = 'rm -r ' + name
    if target_is_file:
        removal_command = 'rm ' + name
    
    if not removal_command is None:
        run_remote_commands(
            logger = logger,
            target = target,
            commands = [
                removal_command
            ]
        )  
        return True
    return False