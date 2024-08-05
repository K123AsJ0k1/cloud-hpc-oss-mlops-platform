from functions.platforms.celery import get_celery_instance
from functions.utility.storage.objects import get_clients
from functions.platforms.celery import get_celery_instance
from functions.utility.collection.management import utilize_artifacts
 
tasks_celery = get_celery_instance()

# Refactored and works 
@tasks_celery.task(   
    bind = False, 
    max_retries = 0,
    soft_time_limit = 120, 
    time_limit = 240,
    rate_limit = '2/m',
    name = 'tasks.sacct-collector'
)
def sacct_collector( 
    configuration
): 
    try:   
        print('Collecting saccts per backend request')
        storage_clients = get_clients(
            configuration = configuration
        )
        storage_names = configuration['storage-names']

        utilize_artifacts(
            storage_client = storage_clients[0],
            storage_name = storage_names[0],
            type = 'sacct'
        ) 

        return True
    except Exception as e:
        print('Sacct collector error:' + str(e))
        return False
# Refactored and works
@tasks_celery.task( 
    bind = False, 
    max_retries = 0,
    soft_time_limit = 120,
    time_limit = 240,
    rate_limit = '2/m',
    name = 'tasks.seff-collector'
)
def seff_collector( 
    configuration
):
    try:  
        print('Collecting seff per backend request')

        storage_clients = get_clients(
            configuration = configuration
        )
        storage_names = configuration['storage-names']

        utilize_artifacts(
            storage_client = storage_clients[0],
            storage_name = storage_names[0],
            type = 'seff'
        )

        return True
    except Exception as e:
        print('Seff collector error:' + str(e))
        return False
    