import time
from functions.management.objects import get_objects, get_folder_objects, set_objects
from functions.metrics.monitor import set_prometheus_metrics

# Refactored and works
def collect_time_dict(
    prometheus_metrics: any,
    time_data: any,
    collector: str,
    area: str
) -> any:
    for id,sample in time_data.items():
        formatted_metadata = {
            'sample-id': id,
            'collector': collector,
            'area': area,
            'action': sample['name'],
            'start': sample['start-time'],
            'end': sample['end-time']
        }

        formatted_metrics = {
            'total-seconds': sample['total-seconds']
        }
        
        set_prometheus_metrics(
            prometheus_metrics = prometheus_metrics,
            type = 'time',
            metadata = formatted_metadata,
            metrics = formatted_metrics
        )
# Refactored and works
def gather_name_times(
    file_lock: any,
    logger: any,
    prometheus_metrics: any,
    allas_client: any,
    allas_bucket: str
):
    # This might be a bit slow on larger objects
    objects = get_folder_objects(
        file_lock = file_lock,
        allas_client = allas_client,
        allas_bucket = allas_bucket,
        object = 'monitor-object',
        replacers = {
            'purpose': 'MONITOR',
            'object': 'TIMES'
        }
    )

    if 0 < len(objects):
        monitor_status = get_objects(
            file_lock = file_lock,
            allas_client = allas_client,
            allas_bucket = allas_bucket,
            object = 'monitor-status',
            replacers = {}
        )

        if not monitor_status is None:
            times = monitor_status['porter-times']
            for name in objects.keys():
                data_dict = objects[name]
                index_key = name + '-index' 
                
                checked_keys = 0
                if not index_key in times:
                    times[index_key] = 0
                else:
                    checked_keys = times[index_key]
                amount_of_keys = len(data_dict)

                if checked_keys < amount_of_keys:
                    starting_key = checked_keys + 1
                    given_dict = {}
                    for key in range(starting_key, amount_of_keys + 1):
                        given_dict[key] = data_dict[str(key)]
                    if 0 < len(given_dict):
                        collect_time_dict(
                            prometheus_metrics = prometheus_metrics,
                            time_data = given_dict,
                            collector = 'porter',
                            area = name
                        )
                        logger.info('The keys of ' + str(name) + ' checked in range ' + str(checked_keys) + '-' + str(amount_of_keys))
                times[index_key] = amount_of_keys
                
            monitor_status['porter-times'] = times
            set_objects(
                file_lock = file_lock,
                allas_client = allas_client,
                allas_bucket = allas_bucket,
                object = 'monitor-status',
                replacers = {},
                overwrite = True,
                object_data = monitor_status
            )
# Refactored and works
def gather_user_times(
    file_lock: any,
    logger: any,
    prometheus_metrics: any,
    allas_client: any,
    allas_bucket: str,
    type: str
):
    submitters_status = get_objects(
        file_lock = file_lock,
        allas_client = allas_client,
        allas_bucket = allas_bucket,
        object = 'submitters-status',
        replacers = {}
    )

    monitor_status = get_objects(
        file_lock = file_lock,
        allas_client = allas_client,
        allas_bucket = allas_bucket,
        object = 'monitor-status',
        replacers = {}
    )
    
    times = None
    if type == 'SUBMITTER':
        times = monitor_status['submitter-times']
    if type == 'BRIDGE':
        times = monitor_status['bridge-times']
    
    if not submitters_status is None and not monitor_status is None and not times is None:
        for kubeflow_user in submitters_status.keys():
            object_name = None
            replacers = None
            if type == 'SUBMITTER':
                object_name = 'submitters-object'
                replacers = {
                    'purpose': 'MONITOR',
                    'folder': kubeflow_user,
                    'object': 'TIMES'
                }
            if type == 'BRIDGE':
                object_name = 'bridge-folder'
                replacers = {
                    'purpose': 'TIMES'
                }

            objects = get_folder_objects(
                file_lock = file_lock,
                allas_client = allas_client,
                allas_bucket = allas_bucket,
                object = object_name,
                replacers = replacers
            )

            if 0 < len(objects):
                if not kubeflow_user in times:
                    times[kubeflow_user] = {}

                for name in objects.keys():
                    data_dict = None
                    if type == 'SUBMITTER':
                        data_dict = objects[name]
                    if type == 'BRIDGE':
                        data_dict = objects[name][kubeflow_user]
                    index_key = name + '-index'
                    
                    checked_keys = 0
                    if not index_key in times[kubeflow_user]:
                        times[kubeflow_user][index_key] = 0
                    else:
                        checked_keys = times[kubeflow_user][index_key]
                    amount_of_keys = len(data_dict)
                    starting_amount = checked_keys
                    if checked_keys < amount_of_keys:
                        starting_key = checked_keys + 1
                        given_dict = {}
                        for key in range(starting_key, amount_of_keys + 1):
                            sample = data_dict[str(key)]
                            if 0 < sample['start-time'] and 0 < sample['end-time'] and 0 < sample['total-seconds']:
                                given_dict[key] = sample
                                checked_keys += 1
                                continue
                            if 0 <= sample['start-time'] and 0 == sample['end-time'] and 0 == sample['total-seconds'] and key == amount_of_keys:
                                break
                            checked_keys += 1
                        user_submitter = kubeflow_user + '-submitter' 
                        if 0 < len(given_dict):
                            collect_time_dict(
                                prometheus_metrics = prometheus_metrics,
                                time_data = given_dict,
                                collector = user_submitter,
                                area = name
                            )
                            logger.info('The keys of ' + str(user_submitter) + '-' + str(type) + '-' + str(name) + ' checked in range ' + str(starting_amount) + '-' + str(checked_keys))
                    
                    times[kubeflow_user][index_key] = checked_keys
                
                if type == 'SUBMITTER':
                    monitor_status['submitter-times'] = times
                if type == 'BRIDGE':
                    monitor_status['bridge-times'] = times
                
                set_objects(
                    file_lock = file_lock,
                    allas_client = allas_client,
                    allas_bucket = allas_bucket,
                    object = 'monitor-status',
                    replacers = {},
                    overwrite = True,
                    object_data = monitor_status
                )