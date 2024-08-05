def format_sacct_command(
    category: str,
    job_id: str
):
    resource_fields = [
        'AveCPU',
        'AveCPUFreq',
        'AveDiskRead',
        'AveDiskWrite',
        'AvePages',
        'AveRSS',
        'AveVMSize',
        'ConsumedEnergyRaw'
    ]

    time_fields = [
        'Timelimit',
        'Submit',
        'Start',
        'Elapsed',
        'Planned',
        'End',
        'PlannedCPU',
        'CPUTime',
        'TotalCPU'
    ]

    used_fields = None
    if category == 'resource':
        used_fields = resource_fields
    if category == 'time':
        used_fields = time_fields
    
    sacct_command = 'sacct -o '
    i = 0 
    for field in used_fields:
        if len(used_fields) == i + 1:
            sacct_command += field
            break
        sacct_command += field + ','
        i += 1 

    sacct_command += ' -j ' + job_id
    return sacct_command