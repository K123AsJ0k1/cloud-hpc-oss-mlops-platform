# Refactored and works
def set_prometheus_metrics( 
    prometheus_metrics: any,
    type: str,
    metadata: any,
    metrics: any
):
    if type == 'seff':
        sample_id = metadata['sample-id']
        user = metadata['user']
        job_id = metadata['job-id']
        job_name = metadata['job']
        project = metadata['billed-project']
        cluster = metadata['cluster']
        status = metadata['status']
        exit_code = metadata['exit-code']
        state = status + '-' + exit_code
        
        for key,value in metrics.items():
            metric_name = prometheus_metrics['seff-name'][key]
            prometheus_metrics['seff'].labels(
                sampleid = sample_id,
                user = user,
                jobid = job_id,
                jobname = job_name,
                project = project,
                cluster = cluster,
                state = state,
                metric = metric_name
            ).set(value)
    if type == 'sacct':
        sample_id = metadata['sample-id']
        row = metadata['row']
        user = metadata['user']
        job_id = metadata['job-id']
        job_name = metadata['job']
        partition = metadata['partition']
        state = metadata['state']
        
        for key,value in metrics.items():
            metric_name = prometheus_metrics['sacct-name'][key]
            prometheus_metrics['sacct'].labels(
                sampleid = sample_id,
                row = row,
                user = user,
                jobid = job_id,
                jobname = job_name,
                partition = partition,
                state = state,
                metric = metric_name
            ).set(value)
    if type == 'time':
        sample_id = metadata['sample-id']
        collector = metadata['collector']
        area = metadata['area']
        action = metadata['action']
        
        for key,value in metrics.items():
            metric_name = prometheus_metrics['time-name'][key]
            prometheus_metrics['time'].labels(
                sampleid = sample_id,
                collector = collector,
                area = area,
                action = action,
                metric = metric_name
            ).set(value)
