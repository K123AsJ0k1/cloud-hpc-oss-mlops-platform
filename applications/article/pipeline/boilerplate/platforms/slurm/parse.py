def parse_job_sacct(
    logger: any,
    sacct: any
) -> any:
    collected_parameters = {}
    collected_metrics = {}
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
    return collected_parameters, collected_metrics

def parse_job_seff(
    logger: any,
    seff: any
) -> any:
    collected_parameters = {}
    collected_metrics = {}
    relevant_metadata = [
        'billed-project',
        'cluster',
        'status'
    ]

    logger.info('')
    logger.info('Seff:')
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

    return collected_parameters, collected_metrics

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
    seff,sacct,logs = get_job_artifacts(
        proxy_url = proxy_url,
        kubeflow_user = kubeflow_user,
        slurm_job_id = slurm_job_id,
        target = proxy_target
    )

    relevant_metadata = [
        'billed-project',
        'cluster',
        'status'
    ]
    
    if not seff is None:
        logger.info('')
        logger.info('Seff:')
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
    
    if not sacct is None:            
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