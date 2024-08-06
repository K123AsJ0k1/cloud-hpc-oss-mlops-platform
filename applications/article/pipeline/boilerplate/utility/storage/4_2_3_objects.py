# Created and works
def set_object_path(
    object_name: str,
    path_replacers: any,
    path_names: any
):
    object_paths = {
        'root': 'name',
        'code': 'CODE/name',
        'slurm': 'CODE/SLURM/name',
        'ray': 'CODE/RAY/name',
        'data': 'DATA/name',
        'artifacts': 'ARTIFACTS/name',
        'time': 'TIME/name'
    }

    i = 0
    path_split = object_paths[object_name].split('/')
    for name in path_split:
        if name in path_replacers:
            replacer = path_replacers[name]
            if 0 < len(replacer):
                path_split[i] = replacer
        i = i + 1
    
    if not len(path_names) == 0:
        path_split.extend(path_names)

    object_path = '/'.join(path_split)
    print('Used object path:' + str(object_path))
    return object_path
# created and works
def setup_storage(
    storage_parameters: any
) -> any:
    storage_client = setup_storage_client(
        storage_parameters = storage_parameters
    ) 
    
    storage_name = set_bucket_name(
       storage_parameters = storage_parameters
    )
    
    return storage_client, storage_name
# Created and works
def check_object(
    storage_client: any,
    bucket_name: str,
    object_name: str,
    path_replacers: any,
    path_names: any
) -> bool:
    object_path = set_object_path(
        object_name = object_name,
        path_replacers = path_replacers,
        path_names = path_names
    )
    # Consider making these functions object storage agnostic
    object_metadata = check_object_metadata(
        storage_client = storage_client,
        bucket_name = bucket_name,
        object_path = object_path
    )
    object_metadata['path'] = object_path
    return object_metadata
# Created and works
def get_object(
    storage_client: any,
    bucket_name: str,
    object_name: str,
    path_replacers: any,
    path_names: any
) -> any:
    checked_object = check_object(
        storage_client = storage_client,
        bucket_name = bucket_name,
        object_name = object_name,
        path_replacers = path_replacers,
        path_names = path_names
    )

    object_data = None
    if not len(checked_object['general-meta']) == 0:
        # Consider making these functions object storage agnostic
        object_data = get_object_content(
            storage_client = storage_client,
            bucket_name = bucket_name,
            object_path = checked_object['path']
        )

    return object_data
# Created and Works
def set_object(
    storage_client: any,
    bucket_name: str,
    object_name: str,
    path_replacers: any,
    path_names: any,
    overwrite: bool,
    object_data: any,
    object_metadata: any
):
    checked_object = check_object(
        storage_client = storage_client,
        bucket_name = bucket_name,
        object_name = object_name,
        path_replacers = path_replacers,
        path_names = path_names
    )
    
    perform = True
    if not len(checked_object['general-meta']) == 0 and not overwrite:
        perform = False
    
    if perform:
        # Consider making these functions object storage agnostic
        create_or_update_object(
            storage_client = storage_client,
            bucket_name = bucket_name,
            object_path = checked_object['path'],
            object_data = object_data,
            object_metadata = object_metadata
        )
# Created and works
def check_bucket(
    storage_client: any,
    bucket_name: str
) -> any:
    return get_bucket_info(
        storage_client = storage_client,
        bucket_name = bucket_name
    )
# Created and works
def check_buckets(
    storage_client: any
) -> any:
    return get_container_info( 
        storage_client = storage_client
    )