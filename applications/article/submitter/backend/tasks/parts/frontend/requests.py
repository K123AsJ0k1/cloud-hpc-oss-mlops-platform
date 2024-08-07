from functions.utility.storage.objects import get_clients
from functions.platforms.celery import get_celery_instance
from functions.utility.storage.jobs import store_created_job, store_started_job, store_stopped_job

tasks_celery = get_celery_instance()

# Refactored and works 
@tasks_celery.task(
    bind = False, 
    max_retries = 0,
    soft_time_limit = 120,
    time_limit = 240,
    rate_limit = '1/m',
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
        storage_names = configuration['storage-names']
        
        return store_created_job( 
            storage_client = storage_clients[0],
            storage_name = storage_names[0],
            job_request = job_request
        )
    except Exception as e:
        print('Create job error: ' + str(e))
        return {'key': '0'}
# Refactored and works
@tasks_celery.task(
    bind = False, 
    max_retries = 0,
    soft_time_limit = 120,
    time_limit = 240,
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
        storage_names = configuration['storage-names']

        return store_started_job(
            storage_client = storage_clients[0],
            storage_name = storage_names[0],
            job_start = job_start
        )
    except Exception as e:
        print('Start job error: ' + str(e))
        return {'status': 'fail'}
# Refactored and works
@tasks_celery.task(
    bind = False, 
    max_retries = 1,
    soft_time_limit = 120,
    time_limit = 240,
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
        
        storage_names = configuration['storage-names']
        
        return store_stopped_job(
            storage_client = storage_clients[0],
            storage_name = storage_names[0],
            job_cancel = job_cancel
        )
    except Exception as e:
        print('Stop job error: ' + str(e))
        return {'status': 'fail'}