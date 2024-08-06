
from functions.platforms.celery import get_signature_id, await_signature
# created and works
def setup_pessimistic_strategy(
    celery_client: any,
    configuration: any
) -> bool:
    # 1 thread required
    task_data = await_signature(
        celery_client = celery_client,
        task_name = 'tasks.template-handler', 
        task_kwargs ={ 
            'configuration': configuration
        },
        timeout = 240 
    )

    if not task_data['result']: 
        return False

    task_data = await_signature(
        celery_client = celery_client,
        task_name = 'tasks.enviroment-handler',
        task_kwargs ={ 
            'configuration': configuration
        },
        timeout = 480
    )
    
    return task_data['result'] 
# created
def submitting_pessimistic_strategy(
    celery_client: any,
    configuration: any
) -> bool:
    # 1 thread required
    # this can duplicate 
    task_data = await_signature(
        celery_client = celery_client,
        task_name = 'tasks.configuration-handler', 
        task_kwargs ={ 
            'configuration': configuration
        },
        timeout = 480 
    ) 

    if not task_data['result']: 
        return False

    task_data = await_signature(
        celery_client = celery_client,
        task_name = 'tasks.monitoring-handler',
        task_kwargs ={ 
            'configuration': configuration
        },
        timeout = 480
    )

    if not task_data['result']: 
        return False

    task_data = await_signature(
        celery_client = celery_client,
        task_name = 'tasks.collections-handler',
        task_kwargs ={ 
            'configuration': configuration
        },
        timeout = 480
    )
    
    return task_data['result']