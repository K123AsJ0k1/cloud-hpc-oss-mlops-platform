from functions.platforms.celery import get_celery_instance
from functions.utility.storage.objects import get_clients
from functions.platforms.celery import get_celery_instance
from functions.utility.collection.management import utilize_time

tasks_celery = get_celery_instance()
 
# Refactored and works 
@tasks_celery.task( 
    bind = False, 
    max_retries = 0,
    soft_time_limit = 120,
    time_limit = 240,
    rate_limit = '2/m',
    name = 'tasks.job-time-collector'
)
def job_time_collector( 
    configuration
):
    try:   
        print('Collecting job times per backend request')

        storage_clients = get_clients(
            configuration = configuration
        )
        storage_names = configuration['storage-names']

        utilize_time(
            storage_client = storage_clients[0],
            storage_name = storage_names[0],
            type = 'job-time'
        )

        return True
    except Exception as e:
        print('Job time collector error:' + str(e))
        return False
# Refactored and works
@tasks_celery.task( 
    bind = False,  
    max_retries = 0,
    soft_time_limit = 120,
    time_limit = 240,
    rate_limit = '2/m',
    name = 'tasks.pipeline-time-collector'
)
def pipeline_time_collector( 
    configuration
):
    try:   
        print('Collecting job times per backend request')

        storage_clients = get_clients(
            configuration = configuration
        )
        storage_names = configuration['storage-names']

        utilize_time(
            storage_client = storage_clients[0],
            storage_name = storage_names[0],
            type = 'pipeline-time'
        )

        return True
    except Exception as e:
        print('Pipeline time collector error:' + str(e))
        return False
# Refactored and works
@tasks_celery.task( 
    bind = False, 
    max_retries = 0,
    soft_time_limit = 120,
    time_limit = 240,
    rate_limit = '2/m',
    name = 'tasks.task-time-collector'
)
def task_time_collector( 
    configuration
):
    try:   
        print('Collecting task times per backend request')
        
        storage_clients = get_clients(
            configuration = configuration
        )
        storage_names = configuration['storage-names']

        utilize_time(
            storage_client = storage_clients[0],
            storage_name = storage_names[0],
            type = 'task-time'
        )

        return True
    except Exception as e:
        print('Task time collector error:' + str(e))
        return False
