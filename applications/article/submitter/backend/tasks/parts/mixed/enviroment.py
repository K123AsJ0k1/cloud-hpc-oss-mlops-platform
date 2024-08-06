from functions.utility.storage.objects import get_clients
from functions.utility.setup.enviroment import store_enviroment_data
from functions.platforms.celery import get_celery_instance
 
tasks_celery = get_celery_instance()

# Created and works
@tasks_celery.task( 
    bind = False, 
    max_retries = 0,
    soft_time_limit = 240,
    time_limit = 480,
    rate_limit = '1/m',
    name = 'tasks.enviroment-handler'
)
def enviroment_handler(  
    configuration: any
) -> bool:
    try:  
        print('Gathering enviroment information for backend') 
        storage_clients = get_clients(
            configuration = configuration
        )
        
        storage_names = configuration['storage-names'] 
        secrets_path = configuration['enviroments']['secrets-path']
        # add configuration passed check later
        store_enviroment_data( 
            storage_client = storage_clients[0],
            storage_name = storage_names[0],
            secrets_path = secrets_path,
            enviroment = 'hpc',
            target = 'mahti'
        )

        return True
    except Exception as e:
        print('Enviroment handler error: ' + str(e))
        return False