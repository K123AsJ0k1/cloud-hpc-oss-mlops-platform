import re
from datetime import datetime

from functions.management.objects import get_objects
from functions.general import convert_into_seconds, unit_converter

# Created and works
def fetch_job_status(
    file_lock: any,
    allas_client: any,
    allas_bucket: str,
    kubeflow_user:str
) -> any:
    submitters_status = get_objects(
        file_lock = file_lock,
        allas_client = allas_client,
        allas_bucket = allas_bucket,
        object = 'submitters-status',
        replacers = {}
    )
    user_jobs = None
    if not submitters_status is None:
        if kubeflow_user in submitters_status:
            user_jobs = submitters_status[kubeflow_user]
    return {'job-status': user_jobs}

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
# Created and works
def fetch_job_seff(
    file_lock: any,
    allas_client: any,
    allas_bucket: str,
    kubeflow_user:str,
    job_id: str
) -> any:
    user_seff = get_objects(
        file_lock = file_lock,
        allas_client = allas_client,
        allas_bucket = allas_bucket,
        object = 'user-object',
        replacers = {
            'purpose': 'MONITOR', 
            'username': kubeflow_user,
            'object': 'seff'
        }
    )
    wanted_seff = {'job-seff':{}}
    if not user_seff is None:
        for values in user_seff.values():
            if values['Job ID'] == job_id:
                formatted_metrics, formatted_metadata = parse_seff_dict(
                    seff_data = values
                )
                wanted_seff['job-seff']['metrics'] = formatted_metrics
                wanted_seff['job-seff']['metadata'] = formatted_metadata
    return wanted_seff
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
# Created and works
def fetch_job_sacct(
    file_lock: any,
    allas_client: any,
    allas_bucket: str,
    kubeflow_user:str,
    job_id: str
) -> any:
    user_sacct = get_objects(
        file_lock = file_lock,
        allas_client = allas_client,
        allas_bucket = allas_bucket,
        object = 'user-object',
        replacers = {
            'purpose': 'MONITOR', 
            'username': kubeflow_user,
            'object': 'sacct'
        }
    )
    wanted_sacct = {'job-sacct':{}}
    if not user_sacct is None:
        for rows in user_sacct.values():
            first_row = rows['1']
            if first_row['JobID'] == job_id:
                key = 1
                for sample in rows.values():
                    formatted_metrics, formatted_metadata = parse_sacct_dict(
                        sacct_data = sample
                    )
                    wanted_sacct['job-sacct'][str(key)] = {
                        'metrics': formatted_metrics,
                        'metadata': formatted_metadata
                    }
                    key += 1
    return wanted_sacct
# Created
def fetch_job_logs(
    file_lock: any,
    allas_client: any,
    allas_bucket: str,
    kubeflow_user:str,
    job_id: str
) -> any:
    user_logs = get_objects(
        file_lock = file_lock,
        allas_client = allas_client,
        allas_bucket = allas_bucket,
        object = 'user-object',
        replacers = {
            'purpose': 'LOGS', 
            'username': kubeflow_user,
            'object': job_id
        }
    )
    wanted_logs = {'job-logs': []}
    if not user_logs is None:
        wanted_logs['job-logs'] = user_logs
    return wanted_logs