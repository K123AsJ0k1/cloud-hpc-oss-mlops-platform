from functions.platforms.celery import get_celery_instance, get_celery_logs
from functions.platforms.kubernetes import get_kubernetes_clients, get_cluster_structure
from functions.utility.scheduling.management import modify_scheduling

tasks_celery = get_celery_instance()

# Refactored and works
@tasks_celery.task( 
    bind = False, 
    max_retries = 0,
    soft_time_limit = 120,
    time_limit = 240,
    rate_limit = '2/m',
    name = 'tasks.start-scheduler'
) 
def start_scheduler(
    scheduler_request: any
) -> any:
    # atleast 1 thread needs to be ready any moment
    try:
        print('Starting scheduler per frontend request')

        return modify_scheduling(
            scheduler_request = scheduler_request,
            action = 'start'
        )
    except Exception as e:
        print('Start scheduler error: ' + str(e))
        return {'status': 'fail'}
# Refactored and works
@tasks_celery.task( 
    bind = False, 
    max_retries = 0,
    soft_time_limit = 120,
    time_limit = 240,
    rate_limit = '2/m',
    name = 'tasks.stop-scheduler'
) 
def stop_scheduler() -> any:
    # atleast 1 thread needs to be ready any moment
    try:
        print('Stopping scheduler per frontend request')
        
        return modify_scheduling(
            scheduler_request = {},
            action = 'stop'
        )
    except Exception as e:
        print('Stop scheduler error: ' + str(e))
        return {'status': 'fail'}