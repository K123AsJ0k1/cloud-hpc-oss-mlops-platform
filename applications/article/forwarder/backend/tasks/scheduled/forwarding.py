from functions.utility.storage.objects import get_clients
from functions.platforms.celery import get_celery_instance
from functions.utility.forwarding.management import deploy_forwards

tasks_celery = get_celery_instance()

# Created and works
@tasks_celery.task(
    bind = False, 
    max_retries = 0,
    soft_time_limit = 480,
    time_limit = 960,
    rate_limit = '1/m',
    name = 'tasks.forwarding-manager'
)
def forwarding_manager(
    configuration: any
) -> any:
    # 1 threads
    # Can cause concurrency issues with other threads
    try:
        print('Forwarding per scheduler request')

        storage_clients = get_clients(
            configuration = configuration
        )
        storage_names = configuration['storage-names']
        
        deploy_forwards(  
            storage_client = storage_clients[0],
            storage_name = storage_names[0]
        )
        
        return True
    except Exception as e:
        print('Forwarding manager error:' + str(e))
        return False
