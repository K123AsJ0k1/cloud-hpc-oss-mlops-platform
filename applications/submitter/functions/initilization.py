from functions.management.objects import get_objects, set_objects

def job_status_template():
    job_status = {
        'job-name': '',
        'job-enviroment': {
            'venv': {
                'name': '',
                'packages': []
            }
        },
        'job-key': '',
        'job-id': '',
        'job-start': False,
        'job-ready': False,
        'job-submit': False,
        'job-pending': False,
        'job-running': False,
        'job-failed': False,
        'job-complete': False,
        'job-cancel': False,
        'job-stored': False
    } 
    return job_status

# Refactored
def initilize_submitter_objects(
    file_lock: any,
    allas_client: any,
    allas_bucket: str,
    kubeflow_user: str
):
    # Check user object concurrency
    objects = {
        'submitters-status': {
            'path': 'submitters-status',
            'replacers': {},
            'template': {
                kubeflow_user: {
                    '1': job_status_template()
                }
            }
        }
    }

    for object in objects.keys():
        path = objects[object]['path']
        replacers = objects[object]['replacers']
        template = objects[object]['template']

        data = get_objects(
            file_lock = file_lock,
            allas_client = allas_client,
            allas_bucket = allas_bucket,
            object = path,
            replacers = replacers
        )
        
        perform = False
        if data is None:
            data = template
            perform = True
        else:
            if not kubeflow_user in data:  
                data[kubeflow_user] = template[kubeflow_user]
                perform = True  
        
        if perform:
            set_objects(
                file_lock = file_lock,
                allas_client = allas_client,
                allas_bucket = allas_bucket,
                object = path,
                replacers = replacers,
                overwrite = True,
                object_data = data
            )