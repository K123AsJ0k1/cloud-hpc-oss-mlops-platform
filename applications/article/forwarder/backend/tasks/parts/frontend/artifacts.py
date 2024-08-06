from functions.platforms.celery import get_celery_instance
from functions.utility.storage.artifacts import get_job_status, get_job_sacct, get_job_seff, get_job_files, get_forwarding_status
from functions.utility.storage.objects import get_clients
from functions.platforms.celery import get_celery_instance

tasks_celery = get_celery_instance() 

# Refactored and works
@tasks_celery.task( 
    bind = False, 
    max_retries = 0,
    soft_time_limit = 60,
    time_limit = 120,
    rate_limit = '2/m',
    name = 'tasks.fetch-job-status'
)
def fetch_job_status( 
    configuration,
    request
):
    # atleast 1 thread needs to be ready any moment
    try:
        print('Fetching job status per frontend request')

        storage_clients = get_clients(
            configuration = configuration
        )
        
        object_store_config = configuration['enviroments']['storage']['object-store']
        bucket_parameters = {
            'bucket-prefix': object_store_config['bucket-prefix'],
            'ice-id': configuration['ice-id'],
            'user': request['user']
        }
        
        del request['user'] 
 
        return get_job_status(
            storage_client = storage_clients[0],
            bucket_parameters = bucket_parameters,
            request = request
        )
    except Exception as e: 
        print('Fetch job status error: ' + str(e))
        return {'job-status': {}}  
# Refactored and works
@tasks_celery.task( 
    bind = False, 
    max_retries = 0,
    soft_time_limit = 60,
    time_limit = 120,
    rate_limit = '2/m',
    name = 'tasks.fetch-job-sacct'
)
def fetch_job_sacct(
    configuration,
    request
):
    # atleast 1 thread needs to be ready any moment
    try:
        print('Fetching job sacct per frontend request')

        storage_clients = get_clients(
            configuration = configuration
        )
        
        object_store_config = configuration['enviroments']['storage']['object-store']
        bucket_parameters = {
            'bucket-prefix': object_store_config['bucket-prefix'],
            'ice-id': configuration['ice-id'],
            'user': request['user']
        }
        
        del request['user']

        return get_job_sacct(
            storage_client = storage_clients[0],
            bucket_parameters = bucket_parameters,
            request = request
        )
    except Exception as e:
        print('Fetch job sacct error: ' + str(e))
        return {'job-sacct': {}}
# Refactored and works
@tasks_celery.task( 
    bind = False, 
    max_retries = 0,
    soft_time_limit = 60,
    time_limit = 120,
    rate_limit = '2/m',
    name = 'tasks.fetch-job-seff'
)
def fetch_job_seff(
    configuration,
    request
):
    # atleast 1 thread needs to be ready any moment
    try:
        print('Fetching job seff per frontend request')

        storage_clients = get_clients(
            configuration = configuration
        )
        
        object_store_config = configuration['enviroments']['storage']['object-store']
        bucket_parameters = {
            'bucket-prefix': object_store_config['bucket-prefix'],
            'ice-id': configuration['ice-id'],
            'user': request['user']
        }
        
        del request['user']

        return get_job_seff(
            storage_client = storage_clients[0],
            bucket_parameters = bucket_parameters,
            request = request
        )
    except Exception as e:
        print('Fetch job seff error: ' + str(e))
        return {'job-seff': {}}
# Refactored and works
@tasks_celery.task( 
    bind = False, 
    max_retries = 0,
    soft_time_limit = 60,
    time_limit = 120,
    rate_limit = '2/m',
    name = 'tasks.fetch-job-files'
)
def fetch_job_files(
    configuration,
    request
):
    # atleast 1 thread needs to be ready any moment
    try:
        print('Fetching job files per frontend request')

        storage_clients = get_clients(
            configuration = configuration
        )
        
        object_store_config = configuration['enviroments']['storage']['object-store']
        bucket_parameters = {
            'bucket-prefix': object_store_config['bucket-prefix'],
            'ice-id': configuration['ice-id'],
            'user': request['user']
        }
        
        del request['user']

        return get_job_files(
            storage_client = storage_clients[0],
            bucket_parameters = bucket_parameters,
            request = request
        )
    except Exception as e:
        print('Fetch job file error: ' + str(e))
        return {'job-files': {}}
# Refactored and works
@tasks_celery.task( 
    bind = False, 
    max_retries = 0,
    soft_time_limit = 120,
    time_limit = 240,
    rate_limit = '2/m',
    name = 'tasks.fetch-forwarding-status'
)
def fetch_forwarding_status(
    configuration,
    request
):
    # atleast 1 thread needs to be ready any moment
    try:
        print('Fetching job files per frontend request')
        
        storage_clients = get_clients(
            configuration = configuration
        )
        
        storage_names = configuration['storage-names']

        object_store_config = configuration['enviroments']['storage']['object-store']
        bucket_parameters = {
            'bucket-prefix': object_store_config['bucket-prefix'],
            'ice-id': configuration['ice-id'],
            'user': request['user']
        }
        
        del request['user']
  
        return get_forwarding_status(
            storage_client = storage_clients[0],
            storage_name = storage_names[0],
            bucket_parameters = bucket_parameters,
            request = request
        )
    except Exception as e:
        print('Fetch job file error: ' + str(e))
        return {'forwarding-status':{}}
