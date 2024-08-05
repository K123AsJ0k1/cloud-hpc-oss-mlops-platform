from functions.utility.storage.objects import get_clients
from functions.platforms.celery import get_celery_instance
from functions.utility.storage.jobs import store_created_job, store_started_job, store_stopped_job
from functions.utility.storage.forwarding import store_created_forwarding, store_stopped_forwarding

tasks_celery = get_celery_instance()

# Refactored and works 
@tasks_celery.task( 
    bind = False, 
    max_retries = 0,
    soft_time_limit = 60,
    time_limit = 120,
    rate_limit = '2/m',
    name = 'tasks.create-job' 
)
def create_job( 
    configuration,
    job_request 
) -> any:
    # Only concurrency issue is with keys
    try:
        print('Creating a job from frontend request')

        storage_clients = get_clients(
            configuration = configuration
        ) 
        
        object_store_config = configuration['enviroments']['storage']['object-store']
        bucket_parameters = {
            'bucket-prefix': object_store_config['bucket-prefix'],
            'ice-id': configuration['ice-id'],
            'user': job_request['user']
        }

        del job_request['user']
        
        return store_created_job( 
            storage_client = storage_clients[0],
            bucket_parameters = bucket_parameters,
            job_request = job_request
        )
    except Exception as e:
        print('Create job error: ' + str(e))
        return {'key': 'none'}
# Refactored and works
@tasks_celery.task(
    bind = False, 
    max_retries = 0,
    soft_time_limit = 60,
    time_limit = 120,
    rate_limit = '2/m',
    name = 'tasks.start-job'
)
def start_job(
    configuration,
    job_start
) -> any:
    # Only concurrency issue is with keys
    # Start Job time here
    try:
        print('Starting a job from frontend request')

        storage_clients = get_clients(
            configuration = configuration
        )
        
        object_store_config = configuration['enviroments']['storage']['object-store']
        bucket_parameters = {
            'bucket-prefix': object_store_config['bucket-prefix'],
            'ice-id': configuration['ice-id'],
            'user': job_start['user']
        }

        del job_start['user']

        return store_started_job(
            storage_client = storage_clients[0],
            bucket_parameters = bucket_parameters,
            job_start = job_start
        )
    except Exception as e:
        print('Start job error: ' + str(e))
        return {'status': 'fail'}
# Refactored and works
@tasks_celery.task(
    bind = False, 
    max_retries = 0,
    soft_time_limit = 60,
    time_limit = 120,
    rate_limit = '2/m',
    name = 'tasks.stop-job'
)
def stop_job(
    configuration,
    job_cancel
):
    # Might need sanitazation
    # Can cause concurrency issues for submitter
    try:
        print('Stopping a job from frontend request')

        storage_clients = get_clients(
            configuration = configuration
        )
        
        object_store_config = configuration['enviroments']['storage']['object-store']
        bucket_parameters = {
            'bucket-prefix': object_store_config['bucket-prefix'],
            'ice-id': configuration['ice-id'],
            'user': job_cancel['user']
        }

        del job_cancel['user']
        
        return store_stopped_job(
            storage_client = storage_clients[0],
            bucket_parameters = bucket_parameters,
            job_cancel = job_cancel
        )
    except Exception as e:
        print('Stop job error: ' + str(e))
        return {'status': 'fail'}
# Created and works
@tasks_celery.task(
    bind = False, 
    max_retries = 0,
    soft_time_limit = 60,
    time_limit = 120,
    rate_limit = '2/m',
    name = 'tasks.create-forwarding'
)
def create_forwarding(
    configuration: any,
    forwarding_request: any
) -> any:
    # Only concurrency issue is with keys

    # There are import and export connections
    # Import connections are outside the cluster forwarder into the cluster
    # Export connections are inside the cluster forwarder outside the cluster

    try:
        print('Creating a forward from frontend request')

        storage_clients = get_clients(
            configuration = configuration
        )
        
        storage_names = configuration['storage-names'] 

        object_store_config = configuration['enviroments']['storage']['object-store']
        bucket_parameters = {
            'bucket-prefix': object_store_config['bucket-prefix'],
            'ice-id': configuration['ice-id'],
            'user': forwarding_request['user']
        } 

        return store_created_forwarding(
            storage_client = storage_clients[0],
            storage_name = storage_names[0],
            forwarding_request = forwarding_request,
            bucket_parameters = bucket_parameters,
        )
    except Exception as e:
        print('Create forwarding error: ' + str(e))
        return {'keys': 'none'}
# Created and works
@tasks_celery.task(
    bind = False, 
    max_retries = 0,
    soft_time_limit = 60,
    time_limit = 120,
    rate_limit = '2/m',
    name = 'tasks.stop-forwarding'
)
def stop_forwarding(
    configuration: any,
    forwarding_cancel: any
) -> any:
    # Can cause concurrency issues with celery workers 
    # Might need sanitazation
    try:
        print('Stopping a forward from frontend request')
        
        storage_clients = get_clients(
            configuration = configuration
        )

        storage_names = configuration['storage-names']

        object_store_config = configuration['enviroments']['storage']['object-store']
        bucket_parameters = {
            'bucket-prefix': object_store_config['bucket-prefix'],
            'ice-id': configuration['ice-id'],
            'user': forwarding_cancel['user'] 
        }
        
        return store_stopped_forwarding(
            storage_client = storage_clients[0],
            storage_name = storage_names[0],
            forwarding_cancel = forwarding_cancel,
            bucket_parameters = bucket_parameters,
        )
    except Exception as e:
        print('Stop forwarding error: ' + str(e))
        return {'status': 'fail'}