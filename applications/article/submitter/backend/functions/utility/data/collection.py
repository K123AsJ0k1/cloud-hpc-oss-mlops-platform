from functions.platforms.celery import get_signature_id

# Created and works
def collect_objects(    
    configuration: any 
): 
    get_signature_id(
        task_name = 'tasks.artifact-handler',
        task_kwargs = {
            'configuration': configuration 
        }
    )  