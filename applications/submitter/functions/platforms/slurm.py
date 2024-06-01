from functions.platforms.ssh import run_remote_commands, download_file
# Refactored and works
def set_file_path(
    object: str,
    job_id: str
):
    artifact_folder = 'artifacts'
    file_paths = {
        'squeue': artifact_folder + '/squeue.txt',
        'sacct': artifact_folder + '/sacct_id.txt',
        'seff': artifact_folder + '/seff_id.txt',
        'logs': artifact_folder + '/logs_id.txt'
    }
    object_path = file_paths[object].replace('id', job_id)
    return object_path
# Created
def save_slurm_squeue(
    logger: any,
    target: str,
    csc_user: str
):
    file_paths = set_file_path(
        object = 'squeue',
        job_id = ''
    )
    squeue_command = 'squeue -u ' + csc_user
    
    results = run_remote_commands(
        logger = logger,
        target = target,
        commands = [
            squeue_command
        ] 
    )
    
    if not results[0] is None:
        with open(file_paths, 'w') as f:
            f.write(results[0])
# Refactored and works
def save_slurm_sacct(
    logger: any,
    target: str,
    job_id: str
):
    file_path = set_file_path(
        object = 'sacct',
        job_id = job_id
    )

    metadata_fields = [
        'JobID',
        'JobName',
        'Account',
        'Partition',
        'ReqCPUS',
        'AllocCPUs',
        'ReqNodes',
        'AllocNodes',
        'State'
    ]

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

    used_fields = metadata_fields + resource_fields + time_fields

    sacct_command = 'sacct -o '
    i = 0 
    for field in used_fields:
        if len(used_fields) == i + 1:
            sacct_command += field
            break
        sacct_command += field + ','
        i += 1 

    sacct_command += ' -j ' + job_id
    
    results = run_remote_commands(
        logger = logger,
        target = target,
        commands = [
            sacct_command
        ] 
    )
    
    if not results[0] is None:
        with open(file_path, 'w') as f:
            f.write(results[0])
# Refactored and works
def save_slurm_seff(
    logger: any,
    target: str,
    job_id: str
):
    file_path = set_file_path(
        object = 'seff',
        job_id = job_id
    )
    seff_command = 'seff ' + job_id
    results = run_remote_commands(
        logger = logger,
        target = target,
        commands = [
            seff_command
        ] 
    )

    if not results[0] is None:
        with open(file_path, 'w') as f:
            f.write(results[0])
# Refactor and works
def save_slurm_log(
    logger: any,
    target: str,
    job_id: str
):  
    file_path = set_file_path(
        object = 'logs',
        job_id = job_id
    )
    job_log_name = 'slurm-' + job_id + '.out'
    
    download_file(
        logger = logger,
        target = target,
        given_local_path = file_path,
        remote_file_name = job_log_name
    )
    # Maybe add log removal
# Check
def parse_slurm_squeue() -> any:
    squeue_print = None
    file_path = set_file_path(
        object = 'squeue',
        job_id = ''
    )
    with open(file_path, 'r') as f:
        squeue_print = f.readlines()

    row_list = []
    for line in squeue_print:
        row = line.split(' ')
        filtered_row = [s for s in row if s != '']
        if not len(row) == 1:
            filtered_row[-1] = filtered_row[-1].replace('\n','')
            row_list.append(filtered_row)
    
    header_dict = {}
    i = 1
    for key in row_list[0]:
        header_dict[str(i)] = key
        i = i + 1

    values_dict = {}
    if 1 < len(row_list):
        i = 1
        for values in row_list[1:]:
            j = 1
            values_dict[i] = {}
            for value in values:
                key = header_dict[str(j)]
                values_dict[i][key] = value
                j = j + 1
            i = i + 1 
    return values_dict
# Refactored and works
def parse_slurm_sacct(
    job_id: str
) -> any: 
    file_path = set_file_path(
        object = 'sacct',
        job_id = job_id
    )

    sacct_print = None
    with open(file_path, 'r') as f:
        sacct_print = f.readlines()

    header = sacct_print[0].split(' ')[:-1]
    columns = [s for s in header if s != '']

    spaces = sacct_print[1].split(' ')[:-1]
    space_sizes = []
    for space in spaces:
        space_sizes.append(len(space))

    values_dict = {}
    rows = sacct_print[2:]
    if 1 < len(sacct_print):
        for i in range(1,len(rows) + 1):
            values_dict[str(i)] = {} 
            for column in columns:
                values_dict[str(i)][column] = ''
        i = 1
        for row in rows:
            start = 0
            end = 0
            j = 0
            
            for size in space_sizes:
                end += size
                formatted_value = [s for s in row[start:end].split(' ') if s != '']
                column_value = None
                if 0 < len(formatted_value):
                    column_value = formatted_value[0] 
                column = columns[j]
                values_dict[str(i)][column] = column_value
                start = end
                end += 1
                j += 1
            i += 1
    return values_dict
# Refactored and works
def parse_slurm_seff(
    job_id: str
) -> any:
    seff_print = None
    file_path = set_file_path(
        object = 'seff',
        job_id = job_id
    )
    with open(file_path, 'r') as f:
        seff_print = f.readlines()
    values_dict = {}
    for line in seff_print:
        if not ':' in line:
            continue 
        filtered = line.replace('\n','')
        
        landmark_indexes = [idx for idx, item in enumerate(filtered.lower()) if ':' in item]
        
        key = filtered[:landmark_indexes[0]]
        value = filtered[landmark_indexes[0]+2:] 

        #formatted_key = key.lower().replace(' ', '-').replace('/', '-')
        # There are additions that need to be parsed later by porter
        values_dict[key] = value
    return values_dict
# Refactored and works
def parse_slurm_logs(
    job_id: str
) -> any:
    log_text = None
    file_path = set_file_path(
        object = 'logs',
        job_id = job_id
    )
    with open(file_path, 'r') as f:
        log_text = f.readlines()
    row_list = []
    for line in log_text:
        filter_1 = line.replace('\n', '')
        filter_2 = filter_1.replace('\t', ' ')
        filter_3 = filter_2.replace('\x1b', ' ')
        row_list.append(filter_3)
    return row_list 