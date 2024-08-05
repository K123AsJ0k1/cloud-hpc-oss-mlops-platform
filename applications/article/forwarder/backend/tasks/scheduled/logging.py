from functions.utility.storage.objects import get_clients
from functions.platforms.celery import get_celery_instance
from functions.utility.logging.management import collect_logs

tasks_celery = get_celery_instance()

# Created and works
@tasks_celery.task(
    bind = False, 
    max_retries = 0,
    soft_time_limit = 480,
    time_limit = 960,
    rate_limit = '1/m', 
    name = 'tasks.logging-manager'
)
def logging_manager(
    configuration: any
) -> any:
    # Can cause concurrency issues with other threads
    try:
        print('Logging per scheduler request')
         
        storage_clients = get_clients(
            configuration = configuration
        )
        storage_names = configuration['storage-names']

        collect_logs( 
            storage_client = storage_clients[0],
            storage_name = storage_names[0]
        )
          
        return True
    except Exception as e:
        print('Logging manager error:' + str(e))
        return False