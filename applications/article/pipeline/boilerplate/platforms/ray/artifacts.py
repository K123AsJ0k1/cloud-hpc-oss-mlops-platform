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
    
    if not ray_job_artifact_parameters is None:
        collected_artifacts['parameters'] = ray_job_artifact_parameters

    predictions_path = job_parameters['artifact-path'] + '-predictions'
    logger.info('Used predictions path: ' + str(predictions_path))
    ray_job_artifact_predictions = get_object(
        client = allas_client,
        bucket_name = allas_bucket,
        object_path = predictions_path
    )

    if not ray_job_artifact_predictions is None:
        collected_artifacts['predictions'] = ray_job_artifact_predictions

    metrics_path = job_parameters['artifact-path'] + '-metrics'
    logger.info('Used metrics path: ' + str(metrics_path))
    ray_job_artifact_metrics = get_object(
        client = allas_client,
        bucket_name = allas_bucket,
        object_path = metrics_path
    )

    if not ray_job_artifact_metrics is None:
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
    if not ray_job_times is None:
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