import time
from datetime import datetime

from functions.management.objects import get_objects, set_objects
from functions.metrics.monitor import set_prometheus_metrics
from functions.general import convert_into_seconds, unit_converter

# Created and works
def sacct_metric_formatting(
    metric: str
) -> any:
    formatted_name = ''
    first = True
    index = -1
    for character in metric:
        index += 1
        if character.isupper():
            if first:
                first = False
                formatted_name += character
                continue
            if index + 1 < len(metric): 
                if metric[index - 1].islower():
                    formatted_name += '-' + character
                    continue
                if metric[index - 1].isupper() and metric[index + 1].islower():
                    formatted_name += '-' + character
                    continue
        formatted_name += character 
    return formatted_name
# Created and works
def parse_sacct_dict(
    sacct_data:any
):
    formatted_data = {}

    metric_units = {
        'ave-cpu': 'seconds',
        'ave-cpu-freq': 'khz',
        'ave-disk-read': 'bytes',
        'ave-disk-write': 'bytes',
        'ave-rss': 'bytes',
        'ave-vm-size': 'bytes',
        'consumed-energy-raw': 'joule',
        'timelimit': 'seconds',
        'elapsed': 'seconds',
        'planned': 'seconds',
        'planned-cpu': 'seconds',
        'cpu-time': 'seconds',
        'total-cpu': 'seconds',
        'submit': 'time',
        'start': 'time',
        'end': 'time'
    }
   
    for key,value in sacct_data.items():
        spaced_key = sacct_metric_formatting(
            metric = key
        )
        formatted_key = spaced_key.lower()
        
        if formatted_key in metric_units:
            formatted_key += '-' + metric_units[formatted_key]
        
        formatted_data[formatted_key] = value

    ignore = [
        'account'
    ]
    
    metadata = [
        'job-name',
        'job-id',
        'partition',
        'state'
    ]
    
    parsed_metrics = {}
    parsed_metadata = {}
    
    for key in formatted_data.keys():
        key_value = formatted_data[key]

        if key_value is None:
            continue

        if key in ignore:
            continue

        if key in metadata:
            if key == 'job-id':
                key_value = key_value.split('.')[0]
            parsed_metadata[key] = key_value
            continue
        
        if ':' in key_value:
            if 'T' in key_value:
                format = datetime.strptime(key_value, '%Y-%m-%dT%H:%M:%S')
                key_value = round(format.timestamp())
            else:
                key_value = convert_into_seconds(
                    given_time = key_value
                )
        else:
            if 'bytes' in key_value:
                key_value = unit_converter(
                    value = key_value,
                    bytes = True
                )
            else:
                key_value = unit_converter(
                    value = key_value,
                    bytes = False
                )
        parsed_metrics[key] = key_value
    return parsed_metrics, parsed_metadata
# Refactored and works
def collect_sacct_dict(
    prometheus_metrics: any,
    sacct_data: any,
    user: str,
    jobs: str
):
    for id,sample in sacct_data.items():
        partition = ''
        for row, data_dict in sample.items():
           
            formatted_metrics, formatted_metadata = parse_sacct_dict(
                sacct_data = data_dict
            )
            formatted_metadata['sample-id'] = id
            formatted_metadata['row'] = row
            formatted_metadata['user'] = user
            formatted_metadata['job'] = jobs[formatted_metadata['job-id']]
            
            if 'partition' in formatted_metadata:
                partition = formatted_metadata['partition']
            else:
                formatted_metadata['partition'] = partition
            
            set_prometheus_metrics(
                prometheus_metrics = prometheus_metrics,
                type = 'sacct',
                metadata = formatted_metadata,
                metrics = formatted_metrics
            )
# Refactored and works
def gather_submitter_sacct(
    file_lock: any,
    logger: any,
    prometheus_metrics: any,
    allas_client: any,
    allas_bucket: str
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

    if not submitters_status is None and not monitor_status is None:
        metrics = monitor_status['submitter-metrics']
        for kubeflow_user in submitters_status.keys():
            user_sacct = get_objects(
                file_lock = file_lock,
                allas_client = allas_client,
                allas_bucket = allas_bucket,
                object = 'submitters-object',
                replacers = {
                    'purpose': 'MONITOR', 
                    'folder': kubeflow_user,
                    'object': 'sacct'
                }
            )

            if not user_sacct is None:
                job_names = {}
                for key in user_sacct.keys():
                    job_id = submitters_status[kubeflow_user][key]['job-id']
                    job_names[job_id] = submitters_status[kubeflow_user][key]['job-name']

                if not kubeflow_user in metrics:
                    metrics[kubeflow_user] = {}

                index_key = 'sacct-index'
                checked_keys = 0
                if not index_key in metrics[kubeflow_user]:
                    metrics[kubeflow_user][index_key] = 0
                else:
                    checked_keys = metrics[kubeflow_user][index_key]
                amount_of_keys = len(user_sacct)

                if checked_keys < amount_of_keys:
                    starting_key = checked_keys + 1
                    given_dict = {}
                    for key in range(starting_key, amount_of_keys + 1):
                        given_dict[key] = user_sacct[str(key)]
                    if 0 < len(given_dict):
                        collect_sacct_dict(
                            prometheus_metrics = prometheus_metrics,
                            sacct_data = given_dict,
                            user = kubeflow_user,
                            jobs = job_names
                        )
                        logger.info('The keys of sacct-' + str(kubeflow_user) + ' checked in range ' + str(checked_keys) + '-' + str(amount_of_keys))

                metrics[kubeflow_user][index_key] = amount_of_keys
        
                monitor_status['submitter-metrics'] = metrics
                set_objects(
                    file_lock = file_lock,
                    allas_client = allas_client,
                    allas_bucket = allas_bucket,
                    object = 'monitor-status',
                    replacers = {},
                    overwrite = True,
                    object_data = monitor_status
                )