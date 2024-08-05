import time

from functions.management.objects import get_objects, set_objects
# Created and works
def store_action_time(
    file_lock: any,
    allas_client: any,
    allas_bucket: any,
    metadata: any,
    time_start: any,
    action_name: str
):
    time_end = time.time()
    time_diff = (time_end - time_start) 

    action_time = {
        'name': action_name,
        'start-time': time_start,
        'end-time': time_end,
        'total-seconds': round(time_diff,5)
    }

    store_collected_metrics(
        file_lock = file_lock,
        allas_client = allas_client,
        allas_bucket = allas_bucket,
        metadata = metadata,
        metrics = action_time
    )
# createda and works
def store_bridge_time_templates(
    file_lock: any,
    allas_client: any,
    allas_bucket: any,
    kubeflow_user: str
):
    templates = {
        'pipeline': {
            'name': 'bridge-pipeline',
            'start-time': time.time(),
            'end-time': 0,
            'total-seconds': 0
        },
        'job': {
            'name': 'bridge-job',
            'start-time': 0,
            'end-time': 0,
            'total-seconds': 0
        },
        'gather': {
            'name': 'bridge-gather',
            'start-time': 0,
            'end-time': 0,
            'total-seconds': 0
        }
    }

    for key,value in templates.items():
        store_collected_metrics(
        file_lock = file_lock,
        allas_client = allas_client,
        allas_bucket = allas_bucket,
        metadata = {
            'type': 'BRIDGE',
            'area': key,
            'user': kubeflow_user
        },
        metrics = value
    )
# Refactored and works
def store_collected_metrics( 
    file_lock: any,
    allas_client: any,
    allas_bucket: str,
    metadata: any,
    metrics: any
) -> bool: 
    type = metadata['type']
    area = metadata['area']
    set_object = None
    set_replacers = None

    if type == 'METRICS' or type == 'RESOURCES' or type == 'TIMES':
        set_object = 'monitor-file'
        set_replacers = {
            'purpose': 'MONITOR',
            'folder': type,
            'name': area
        } 

    if type == 'BRIDGE':
        set_object = 'bridge-object'
        set_replacers = {
            'purpose': 'TIMES',
            'object': area
        } 

    if not set_object is None:
        current_data = get_objects(
            file_lock = file_lock,
            allas_client = allas_client,
            allas_bucket = allas_bucket,
            object = set_object,
            replacers = set_replacers
        )

        object_data = None
        if current_data is None:
            object_data = {}
        else:
            object_data = current_data

        if type == 'BRIDGE':
            user = metadata['user']
            if not user in object_data:
                object_data[user] = {
                    '1': metrics
                }
            else:
                new_key = len(object_data[user]) + 1
                object_data[user][str(new_key)] = metrics
        else:
            new_key = len(object_data) + 1
            object_data[str(new_key)] = metrics

        set_objects(
            file_lock = file_lock,
            allas_client = allas_client,
            allas_bucket = allas_bucket,
            object = set_object,
            replacers = set_replacers,
            overwrite = True,
            object_data = object_data
        )
    return True