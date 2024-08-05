from datetime import datetime

from allas import get_object, create_or_update_object
from submission import get_job_artifacts

def gather_time(
    logger: any,
    allas_client: any,
    allas_bucket: str,
    kubeflow_user: str,
    time_folder_path: str,
    object_name: str,
    action_name: str,
    start_time: int,
    end_time: int
):
    time_path = time_folder_path + '/' + object_name
    #logger.info('Time object path:' + str(time_path))
    current_data = get_object(
        client = allas_client,
        bucket_name = allas_bucket,
        object_path = time_path
    )

    object_data = None
    if current_data is None:
        object_data = {}
    else:
        object_data = current_data

    if not kubeflow_user in object_data:
        object_data[kubeflow_user] = {}

    user_time_dict = object_data[kubeflow_user]

    current_key_amount = len(user_time_dict)
    current_key_full = False
    current_key = str(current_key_amount)
    if 0 < current_key_amount:
        time_object = user_time_dict[current_key]
        if 0 < time_object['total-seconds']:
            current_key_full = True
    
    changed = False
    if 0 < end_time and 0 < current_key_amount and not current_key_full:
        stored_start_time = user_time_dict[current_key]['start-time']
        time_diff = (end_time-stored_start_time)
        user_time_dict[current_key]['end-time'] = end_time
        user_time_dict[current_key]['total-seconds'] = round(time_diff,5)
        changed = True
    else:
        next_key_amount = len(user_time_dict) + 1
        new_key = str(next_key_amount)
    
        if 0 < start_time and 0 == end_time:
            user_time_dict[new_key] = {
                'name': action_name,
                'start-time': start_time ,
                'end-time': 0,
                'total-seconds': 0
            }
            changed = True

        if 0 < start_time and 0 < end_time:
            time_diff = (end_time-start_time)
            user_time_dict[new_key] = {
                'name': action_name,
                'start-time': start_time,
                'end-time': end_time,
                'total-seconds': round(time_diff,5)
            }
            changed = True

    if changed:
        object_data[kubeflow_user] = user_time_dict
        create_or_update_object(
            client = allas_client,
            bucket_name = allas_bucket,
            object_path = time_path, 
            data = object_data
        )    

def gather_slurm_artifacts(
    logger: any,
    proxy_url: str,
    proxy_target: str,
    kubeflow_user: str,
    slurm_job_id: str
) -> any:
    collected_parameters = {}
    collected_metrics = {}
    
    logger.info('Collecting SLURM artifacts')
    logger.info('')
    seff,sacct,logs = get_job_artifacts(
        proxy_url = proxy_url,
        kubeflow_user = kubeflow_user,
        slurm_job_id = slurm_job_id,
        target = proxy_target
    )

    logger.info('Seff:')

    relevant_metadata = [
        'billed-project',
        'cluster',
        'status'
    ]
    
    seff_metadata = seff['metadata']
    for key,value in seff_metadata.items():
        if key in relevant_metadata:
            logger.info(str(key) + '=' + str(value))
            collected_parameters[key] = value
    
    relevant_metrics = [
        'billing-units',
        'cpu-efficiency-percentage',
        'cpu-efficiency-seconds',
        'cpu-utilized-seconds',
        'job-wall-clock-time-seconds',
        'memory-efficiency-percentage'
    ]
    
    seff_metrics = seff['metrics']
    for key,value in seff_metrics.items():
        if key in relevant_metrics:
            logger.info(str(key) + '=' + str(value))
            collected_metrics[key] = value
    
    logger.info('')
    logger.info('Sacct:')
    for row in sacct.keys():
        logger.info('Row ' + str(row))
        row_metadata = sacct[row]['metadata']
        row_metrics = sacct[row]['metrics']
    
        relevant_metadata = [
            'job-name',
            'state'
        ]
        
        for key, value in row_metadata.items():
            if key in relevant_metadata:
                logger.info(str(key) + '=' + str(value))
                collected_parameters[str(row) + '-' + key] = value
    
        relevant_metrics = [
            'ave-cpu-seconds',
            'cpu-time-seconds',
            'elapsed-seconds',
            'total-cpu-seconds',
        ]
        
        for key, value in row_metrics.items():
            if key in relevant_metrics:
                logger.info(str(key) + '=' + str(value))
                collected_metrics[str(row) + '-' + key] = value
    
        start_time = row_metrics['start-time']
        submit_time = row_metrics['submit-time']
        end_time = row_metrics['end-time']
    
        submit_date = datetime.fromtimestamp(start_time).strftime('%Y-%m-%d-%H:%M:%S')
        total_start_seconds = (submit_time-start_time)
        total_end_seconds = (end_time-submit_time)
    
        logger.info('submit-date=' + str(submit_date))
        collected_parameters[str(row) + '-submit-date'] = submit_date
        
        logger.info('total-submit-start-seconds=' + str(total_start_seconds))
        collected_metrics[str(row) + '-total-submit-start-seconds'] = total_start_seconds
        
        logger.info('total-start-end-seconds=' + str(total_end_seconds))
        collected_metrics[str(row) + '-total-start-end-seconds'] = total_end_seconds
        
        logger.info('')
        
    artifacts = [
        collected_parameters, 
        collected_metrics,
        logs
    ]

    return artifacts

def gather_ray_artifacts(
    logger: any,
    allas_client: any,
    allas_bucket: str,
    kubeflow_user: str,
    ray_parameters: any
):
    collected_parameters = {}
    collected_metrics = {}
    collected_artifacts = {}    
    job_parameters = ray_parameters['job-parameters']

    logger.info('Training hyperparameters:')
    
    for key,value in job_parameters.items():
        if 'hp-' in key:
            formatted_key = key.replace('hp-', '')
            logger.info(str(key) + '=' + str(value))
            collected_parameters[formatted_key] = value

    logger.info('')
    parameters_path = job_parameters['artifact-path'] + '-parameters'
    logger.info('Used parameters path: ' + str(parameters_path))
    ray_job_artifact_parameters = get_object(
        client = allas_client,
        bucket_name = allas_bucket,
        object_path = parameters_path
    )
    collected_artifacts['parameters'] = ray_job_artifact_parameters

    predictions_path = job_parameters['artifact-path'] + '-predictions'
    logger.info('Used predictions path: ' + str(predictions_path))
    ray_job_artifact_predictions = get_object(
        client = allas_client,
        bucket_name = allas_bucket,
        object_path = predictions_path
    )
    collected_artifacts['predictions'] = ray_job_artifact_predictions

    metrics_path = job_parameters['artifact-path'] + '-metrics'
    logger.info('Used metrics path: ' + str(metrics_path))
    ray_job_artifact_metrics = get_object(
        client = allas_client,
        bucket_name = allas_bucket,
        object_path = metrics_path
    )
    performance = ray_job_artifact_metrics['performance']
    logger.info('')
    logger.info('Training metrics:')
    for key,value in performance.items():
        if key == 'name':
            continue
        if 'class-' in key:
            image_labels = {
                0: 'top',
                1: 'trouser',
                2: 'pullover',
                3: 'dress',
                4: 'coat',
                5: 'sandal',
                6: 'shirt',
                7: 'sneaker',
                8: 'bag',
                9: 'ankle-boot',
            }
            logger.info('')
            i = 0
            for class_value in value:
                formatted_key = key.replace('class', image_labels[i])
                rounded_value = round(class_value,5)
                logger.info(str(formatted_key) + '=' + str(rounded_value))
                collected_metrics[formatted_key] = rounded_value
                i += 1
            continue
        rounded_value = round(value,5)
        logger.info(str(key) + '=' + str(rounded_value))
        collected_metrics[key] = rounded_value

    logger.info('')
    time_path = job_parameters['time-folder-path'] + '/ray-job'
    logger.info('Used time path: ' + str(time_path))
    ray_job_times = get_object(
        client = allas_client,
        bucket_name = allas_bucket,
        object_path = time_path
    )

    logger.info('')
    logger.info('Training times:')
    user_ray_job_times = ray_job_times[kubeflow_user]
    for i in range(0,2):
        object_key = len(user_ray_job_times) - i
        time_object = user_ray_job_times[str(object_key)]
        formatted_key = time_object['name'] + '-total-seconds'
        value = time_object['total-seconds']
        collected_metrics[formatted_key] = value
        logger.info(str(formatted_key) + '=' + str(value))
    
    artifacts = [
        collected_parameters, 
        collected_metrics,
        collected_artifacts
    ]

    return artifacts

def gather_bridge_times(
    allas_client: any,
    allas_bucket: str,
    kubeflow_user: str,
    time_folder_path: str
):
    names = [
        'gather',
        'job',
        'pipeline',
        'ray-job',
        'workflow'
    ]

    times = {}
    for name in names:
        used_path = time_folder_path + '/' + name
        given_data = get_object(
            client = allas_client,
            bucket_name = allas_bucket,
            object_path = used_path
        )
        times[name] = {}
        record = 1
        user_data = given_data[kubeflow_user]
        for key,data in user_data.items():
            record_name = data['name']
            record_total = data['total-seconds']
            times[name][str(record)] = {
                'name': record_name,
                'total-seconds': record_total
            }
            record += 1
    return times  

def gather_submitter_times(
    allas_client: any,
    allas_bucket: str,
    kubeflow_user: str
):
    names = [
        'bridge',
        'cancel',
        'jobs',
        'monitor',
        'jobs',
        'setup',
        'submit',
        'task'
    ]

    times = {}
    for name in names:
        used_path = 'BRIDGE/SUBMITTERS/MONITOR/' + kubeflow_user + '/TIMES/' + name
        user_data = get_object(
            client = allas_client,
            bucket_name = allas_bucket,
            object_path = used_path
        )
        times[name] = {}
        record = 1
        for key,data in user_data.items():
            record_name = data['name']
            record_total = data['total-seconds']
            times[name][str(record)] = {
                'name': record_name,
                'total-seconds': record_total
            }
            record += 1
    return times  

def gather_submitter_times(
    allas_client: any,
    allas_bucket: str,
    kubeflow_user: str
):
    names = [
        'bridge',
        'cancel',
        'monitor',
        'setup',
        'submit',
        'task'
    ]

    times = {}
    for name in names:
        used_path = 'BRIDGE/SUBMITTERS/MONITOR/' + kubeflow_user + '/TIMES/' + name
        user_data = get_object(
            client = allas_client,
            bucket_name = allas_bucket,
            object_path = used_path
        )
        times[name] = {}
        record = 1
        for key,data in user_data.items():
            record_name = data['name']
            record_total = data['total-seconds']
            times[name][str(record)] = {
                'name': record_name,
                'total-seconds': record_total
            }
            record += 1
    return times  