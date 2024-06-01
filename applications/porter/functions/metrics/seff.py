import re

from functions.management.objects import get_objects, set_objects
from functions.metrics.monitor import set_prometheus_metrics
from functions.general import convert_into_seconds, unit_converter
# Refactored and works
def parse_seff_dict(
    seff_data: any
):
    parsed_data = {}
    for metric in seff_data.keys():
        formatted_key = re.sub(r'\([A-Z]*\)','',metric).lower().replace(' ','-').replace('/','-')
        value = seff_data[metric]
        
        if 'of' in str(value):
            value_split = value.split('of')
            percentage = value_split[0].replace(' ', '')
            amount = value_split[1].replace(' ', '')
            parsed_data[formatted_key + '-percentage'] = re.sub(r'[%]*','',percentage)
            formatted_value = re.sub(r'[A-Za-z-]*','',amount)
            if ':' in formatted_value:
                parsed_data[formatted_key + '-seconds'] = convert_into_seconds(
                    given_time = formatted_value
                )
                continue
            if 'memory' in formatted_key:
                converted_value = unit_converter(
                    value = amount,
                    bytes = True
                )
                parsed_data[formatted_key + '-bytes'] = converted_value
                continue
            parsed_data[formatted_key + '-amount'] = formatted_value
            continue
            
        if ':' in str(value):
            parsed_data[formatted_key + '-seconds'] = convert_into_seconds(
                given_time = value
            )
            continue
        
        if 'state' in formatted_key:
            value_split = value.split(' ')
            status = value_split[0]
            exit_code = value_split[-1][:-1]
            parsed_data['status'] = status
            parsed_data['exit-code'] = exit_code
            continue
            
        if 'non-interactive-bus' in formatted_key:
            parsed_data['billing-units'] = value
            continue
            
        if 'memory' in formatted_key:
            amount = value.replace(' ', '')
            converted_value = unit_converter(
                value = amount,
                bytes = True
            )
            parsed_data[formatted_key + '-bytes'] = converted_value
            continue
           
        parsed_data[formatted_key] = value
                
    ignore = [
        'user-group'
    ]
    
    metadata = [
        'billed-project',
        'job-id',
        'cluster',
        'status',
        'exit-code'
    ]
    
    parsed_metadata = {}
    parsed_metrics = {}
    for key in parsed_data.keys():
        if key in ignore:
            continue
        if key in metadata:
            parsed_metadata[key] = parsed_data[key]
            continue
        parsed_metrics[key] = parsed_data[key]
    return parsed_metrics, parsed_metadata
# Refactored and works
def collect_seff_dict(
    prometheus_metrics: any,
    seff_data: any,
    user: str,
    jobs: str
):
    for id, sample in seff_data.items():
        formatted_metrics, formatted_metadata = parse_seff_dict(
            seff_data = sample
        )
        formatted_metadata['sample-id'] = id
        formatted_metadata['user'] = user
        # causes problems if submitter status is different
        formatted_metadata['job'] = jobs[formatted_metadata['job-id']]
        
        set_prometheus_metrics(
            prometheus_metrics = prometheus_metrics,
            type = 'seff',
            metadata = formatted_metadata,
            metrics = formatted_metrics
        )
# Refactored and works
def gather_submitter_seff(
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
            
            user_seff = get_objects(
                file_lock = file_lock,
                allas_client = allas_client,
                allas_bucket = allas_bucket,
                object = 'submitters-object',
                replacers = {
                    'purpose': 'MONITOR', 
                    'folder': kubeflow_user,
                    'object': 'seff'
                }
            )

            if not user_seff is None:
                job_names = {}
                for key in user_seff.keys():
                    # causes problems if submitter status is different
                    job_id = submitters_status[kubeflow_user][key]['job-id']
                    job_names[job_id] = submitters_status[kubeflow_user][key]['job-name']

                if not kubeflow_user in metrics:
                    metrics[kubeflow_user] = {}
                
                index_key = 'seff-index'
                checked_keys = 0
                if not index_key in metrics[kubeflow_user]:
                    metrics[kubeflow_user][index_key] = 0
                else:
                    checked_keys = metrics[kubeflow_user][index_key]
                amount_of_keys = len(user_seff)

                if checked_keys < amount_of_keys:
                    starting_key = checked_keys + 1
                    given_dict = {}
                    for key in range(starting_key, amount_of_keys + 1):
                        given_dict[key] = user_seff[str(key)]
                    if 0 < len(given_dict):
                        collect_seff_dict(
                            prometheus_metrics = prometheus_metrics,
                            seff_data = given_dict,
                            user = kubeflow_user,
                            jobs = job_names
                        )
                        logger.info('The keys of seff-' + str(kubeflow_user) + ' checked in range ' + str(checked_keys) + '-' + str(amount_of_keys))

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