from functions.utility.storage.objects import get_clients
from functions.utility.storage.templates import store_templates
from functions.platforms.celery import get_celery_instance
from functions.platforms.redis import get_redis_instance, get_redis_lock, check_redis_lock, release_redis_lock
import time

tasks_celery = get_celery_instance()

# Created and works
@tasks_celery.task(
    bind = False, 
    max_retries = 0,
    soft_time_limit = 240,
    time_limit = 480,
    rate_limit = '1/m',
    name = 'tasks.template-handler'
)
def template_handler( 
    configuration 
):
    # Since we want to have multiple jobs
    # this needs to create a template for porter
    # This also enables us to create code that can handle eventual consistency
    # communication objects should be kept small, while artifact objects should be medium to large
    try:
        print('Handling submitter templates per frontend request')

        redis_client = get_redis_instance()

        lock_name = 'template-handler-lock'

        lock_exists = check_redis_lock(
            redis_client = redis_client,
            lock_name = lock_name
        )
        print('Redis lock exists: ' + str(lock_exists))
        if not lock_exists:
            lock_active, redis_lock = get_redis_lock(
                redis_client = redis_client,
                lock_name = lock_name,
                timeout = 300
            )

            print('Redis lock aquired: ' + str(lock_active))
            if lock_active:
                status = False

                try:  
                    storage_clients = get_clients(
                        configuration = configuration
                    )
                    
                    storage_names = configuration['storage-names']
                    storage_parameters = configuration['enviroments']['storage']
                     
                    store_templates(
                        storage_clients = storage_clients,
                        storage_names = storage_names,
                        storage_parameters = storage_parameters
                    )

                    status = True
                except Exception as e:
                    print('Store templates error: ' + str(e))

                lock_released = release_redis_lock(
                    redis_lock = redis_lock
                )  
                
                print('Redis lock released: ' + str(lock_released))

                return status
            else:
                return False 
        return False
    except Exception as e:
        print('Template handler error:' + str(e))
        return False

            