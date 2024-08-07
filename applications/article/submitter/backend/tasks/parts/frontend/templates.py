from functions.utility.storage.objects import get_clients
from functions.utility.storage.templates import store_templates
from functions.platforms.celery import get_celery_instance

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

        return True
    except Exception as e:
        print('Template handler error:' + str(e))
        return False

            