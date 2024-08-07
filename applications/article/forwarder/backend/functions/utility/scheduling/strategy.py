from functions.platforms.celery import get_signature_id, await_signature
# created
def optimistic_strategy(
    configuration: any
):
    # 5 threads required
    get_signature_id(
        task_name = 'tasks.sacct-collector',
        task_kwargs = {
            'configuration': configuration
        }
    ) 

    get_signature_id( 
        task_name = 'tasks.seff-collector',
        task_kwargs = {
            'configuration': configuration
        }
    )

    get_signature_id(
        task_name = 'tasks.job-time-collector',
        task_kwargs = {
            'configuration': configuration
        }
    )

    get_signature_id(
        task_name = 'tasks.pipeline-time-collector',
        task_kwargs = {
            'configuration': configuration
        }
    )

    get_signature_id(
        task_name = 'tasks.task-time-collector',
        task_kwargs = {
            'configuration': configuration
        }
    )
# created and works
def pessimistic_strategy(
    celery_client: any,
    configuration: any
) -> bool:
    # 1 thread required
    task_data = await_signature(
        celery_client = celery_client,
        task_name = 'tasks.sacct-collector',
        task_kwargs ={ 
            'configuration': configuration
        },
        timeout = 240 
    ) 

    if not task_data['result']: 
        return False

    task_data = await_signature(
        celery_client = celery_client,
        task_name = 'tasks.seff-collector',
        task_kwargs ={ 
            'configuration': configuration
        },
        timeout = 240
    )

    if not task_data['result']: 
        return False

    task_data = await_signature(
        celery_client = celery_client,
        task_name = 'tasks.job-time-collector',
        task_kwargs ={ 
            'configuration': configuration
        },
        timeout = 240
    )
    if not task_data['result']: 
        return False
    
    task_data = await_signature(
        celery_client = celery_client,
        task_name = 'tasks.pipeline-time-collector',
        task_kwargs ={ 
            'configuration': configuration
        },
        timeout = 240
    )
    
    if not task_data['result']: 
        return False 

    task_data = await_signature(
        celery_client = celery_client,
        task_name = 'tasks.task-time-collector',
        task_kwargs ={ 
            'configuration': configuration
        },
        timeout = 240
    )
    
    return task_data['result']