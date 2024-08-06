from functions.platforms.celery import get_celery_instance
from functions.utility.scheduling.strategy import pessimistic_strategy

tasks_celery = get_celery_instance()

# Created and works
@tasks_celery.task(
    bind = False, 
    max_retries = 0,
    soft_time_limit = 480,
    time_limit = 960,
    rate_limit = '1/m',
    name = 'tasks.collection-manager'
)
def collection_manager(  
    configuration: any
) -> any:
    # Can cause concurrency issues with other threads
    # 1 + 5 threads with optimistic
    # 1 + 1 threads with pessimistic
    try:
        print('Collecting per scheduler request')
        
        return pessimistic_strategy(
            celery_client = tasks_celery,
            configuration = configuration
        )
    except Exception as e:
        print('Collection manager error:' + str(e))
        return False
