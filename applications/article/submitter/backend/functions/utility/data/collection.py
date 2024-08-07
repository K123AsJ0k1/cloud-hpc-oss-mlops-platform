from functions.platforms.celery import get_signature_id, await_signature

# Created and works
def collect_objects(    
    celery_client: any,
    configuration: any 
): 
    task_data = await_signature(
        celery_client = celery_client,
        task_name = 'tasks.monitoring-handler',
        task_kwargs ={ 
            'configuration': configuration
        },
        timeout = 500
    ) 
    return task_data['result'] 