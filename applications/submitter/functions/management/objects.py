from functions.platforms.allas import check_object, get_object, create_or_update_object
# Refactored and works
def set_object_path(
    object: str,
    replacers: any
):
    bridge_folder = 'BRIDGE'
    submitters_folder = 'SUBMITTERS'
    
    object_paths = {
        'slurm-job': bridge_folder + '/JOBS/username/SLURM/name',
        'bridge-object': bridge_folder + '/purpose/object',
        'submitters-status': bridge_folder + '/' + submitters_folder + '/status',
        'user-object': bridge_folder + '/' + submitters_folder + '/purpose/username/object',
        'user-file': bridge_folder + '/' + submitters_folder + '/purpose/username/folder/name'
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
# Refactored and works
def get_objects(
    file_lock: any,
    allas_client: any,
    allas_bucket: str,
    object: str,
    replacers: str
) -> any:
    object_data = None
    with file_lock:
        object_path = set_object_path(
            object = object,
            replacers = replacers
        )

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
# Refactored and works
def set_objects(
    file_lock: any,
    allas_client: any,
    allas_bucket: any,
    object: str,
    replacers: str,
    overwrite: bool,
    object_data: any
):
    with file_lock:
        object_path = set_object_path(
            object = object,
            replacers = replacers
        )

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
# Fix and abstrat away object changes