from functions.utility.storage.objects import get_clients
from functions.utility.data.artifacts import collect_artifacts
from functions.platforms.celery import get_celery_instance

tasks_celery = get_celery_instance()

# Created and works 
@tasks_celery.task( 
    bind = False, 
    max_retries = 0,
    soft_time_limit = 480,
    time_limit = 960,
    rate_limit = '1/m',
    name = 'tasks.artifact-handler'
)
def artifact_handler(
    configuration: any
) -> bool:
    try:  
        print('Gathering artifacts for backend') 

        storage_clients = get_clients(
            configuration = configuration
        )
        storage_names = configuration['storage-names']
        secrets_path = configuration['enviroments']['secrets-path']

        collect_artifacts(  
            storage_client = storage_clients[0],
            storage_names = storage_names,
            secrets_path = secrets_path
        ) 

        return True
    except Exception as e:
        print('Artifact handler error: ' + str(e))
        return False