from allas import check_object, get_object, create_or_update_object

def set_object_path(
    object: str,
    replacers: any
):
    bridge_folder = 'BRIDGE'
    object_paths = {
        'slurm': bridge_folder + '/JOBS/username/SLURM/name',
        'ray': bridge_folder + '/JOBS/username/RAY/name'
    }
    
    i = 0
    path_split = object_paths[object].split('/')
    for name in path_split:
        if name in replacers:
            replacer = replacers[name]
            if 2 < len(replacer):
                path_split[i] = replacer
        i = i + 1

    object_path = '/'.join(path_split)
    return object_path
    
def get_objects(
    allas_client: any,
    allas_bucket: str,
    object: str,
    replacers: any
) -> any:
    object_path = set_object_path(
        object = object,
        replacers = replacers
    )
    print('Used object path: ', object_path)
    object_info = check_object(
        client = allas_client,
        bucket_name = allas_bucket,
        object_path = object_path
    )
    
    if not len(object_info) == 0:
        object_data = get_object(
            client = allas_client,
            bucket_name = allas_bucket,
            object_path = object_path
        )
    return object_data
    
def set_objects(
    allas_client: any,
    allas_bucket: str,
    object: str,
    replacers: any,
    overwrite: bool,
    object_data: any
):
    object_path = set_object_path(
        object = object,
        replacers = replacers
    )
    print('Used object path: ', object_path)
    object_info = check_object(
        client = allas_client,
        bucket_name = allas_bucket,
        object_path = object_path
    )
    
    perform = True
    if 0 < len(object_info) and not overwrite:
        perform = False
    
    if perform:
        create_or_update_object(
            client = allas_client,
            bucket_name = allas_bucket,
            object_path = object_path,
            data = object_data
        )

def store_script(
    allas_client: any,
    allas_bucket: str,
    kubeflow_user: str,
    folder_name: str,
    file_name: str
):
    used_path = folder_name + '/' + file_name
    file = None
    
    print('Used file path:' + str(used_path))
    with open(used_path, 'r') as job:
        file = job.read()
    
    name = file_name.split('.')[0]
    if not file is None:
        used_object = None
        used_replacers = None
        
        if 'slurm' in folder_name:
            used_object = 'slurm'
            used_replacers = {
                'username': kubeflow_user,
                'name': name
            }
            
        if 'ray' in folder_name:
            used_object = 'ray'
            used_replacers = {
                'username': kubeflow_user,
                'name': name
            }

        set_objects(
            allas_client = allas_client,
            allas_bucket = allas_bucket,
            object = used_object,
            replacers = used_replacers,
            overwrite = True,
            object_data = file
        )

def get_script(
    allas_client: any,
    allas_bucket: str,
    kubeflow_user: str,
    folder_name: str,
    file_name: str
):
    name = file_name.split('.')[0]
    if 'slurm' in folder_name:
        used_object = 'slurm'
        used_replacers = {
            'username': kubeflow_user,
            'name': name
        }
        
    if 'ray' in folder_name:
        used_object = 'ray'
        used_replacers = {
            'username': kubeflow_user,
            'name': name
        }
    
    fetched_file = get_objects(
        allas_client = allas_client,
        allas_bucket = allas_bucket,
        object = used_object,
        replacers = used_replacers 
    )
    return fetched_file