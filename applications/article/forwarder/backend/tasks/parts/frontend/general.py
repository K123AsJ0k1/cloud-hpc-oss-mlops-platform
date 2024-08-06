from functions.platforms.celery import get_celery_instance, get_celery_logs
from functions.platforms.kubernetes import get_kubernetes_clients, get_cluster_structure

tasks_celery = get_celery_instance()

# Refactored and works
@tasks_celery.task( 
    bind = False, 
    max_retries = 0,
    soft_time_limit = 120,
    time_limit = 240,
    rate_limit = '2/m',
    name = 'tasks.get-logs'
) 
def get_logs() -> any:
    # atleast 1 thread needs to be ready any moment
    try:
        print('Getting logs per frontend request')
        return get_celery_logs()
    except Exception as e:
        print('Get logs error: ' + str(e))
        return {'logs':[]} 
# Refactored and works
@tasks_celery.task( 
    bind = False, 
    max_retries = 0,
    soft_time_limit = 120,
    time_limit = 240,
    rate_limit = '2/m',
    name = 'tasks.get-structure'
) 
def get_structure() -> any:
    # atleast 1 thread needs to be ready any moment
    try:
        print('Getting cluster structure per frontend request')
        kubernetes_clients = get_kubernetes_clients()
        return get_cluster_structure(
            kubernetes_clients = kubernetes_clients
        )
    except Exception as e:
        print('Get structure error: ' + str(e))
        return {'structure': {}}