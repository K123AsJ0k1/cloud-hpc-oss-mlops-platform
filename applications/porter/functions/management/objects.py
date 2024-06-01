from functions.platforms.allas import check_object, get_object, create_or_update_object, get_object_list, remove_object
# Refactored and works
def set_object_path(
    object: str,
    replacers: any
):
    bridge_folder = 'BRIDGE'
    porter_folder = 'PORTER'
    submitters_folder = 'SUBMITTERS'
    
    object_paths = {
        'bridge-folder': bridge_folder + '/purpose',
        'bridge-object': bridge_folder + '/purpose/object',
        'porter-status': bridge_folder + '/' + porter_folder + '/status',
        'monitor-status': bridge_folder + '/' + porter_folder + '/MONITOR/status',
        'monitor-object': bridge_folder + '/' + porter_folder + '/purpose/object',
        'monitor-file': bridge_folder + '/' + porter_folder + '/purpose/folder/name',
        'submitters-status': bridge_folder + '/' + submitters_folder + '/status',
        'submitters-folder': bridge_folder + '/' + submitters_folder + '/purpose/username',
        'submitters-object': bridge_folder + '/' + submitters_folder + '/purpose/folder/object',
        'submitters-file': bridge_folder + '/' + submitters_folder + '/purpose/folder/object/name'
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
    replacers: any
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
    allas_bucket: str,
    object: str,
    replacers: any,
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
# Refactored and works
def get_folder_objects(
    file_lock: any,
    allas_client: any,
    allas_bucket: str,
    object: str,
    replacers: any
) -> any:
    files = {}
    with file_lock:
        object_path = set_object_path(
            object = object,
            replacers = replacers
        )
        
        folder_objects = get_object_list(
            client = allas_client,
            bucket_name = allas_bucket,
            path_prefix = object_path
        )
        # This gets none during long runs
        for file_path in folder_objects.keys():
            formatted_file_path = file_path[:-4]
            file_name = formatted_file_path.split('/')[-1]
            file_data = get_object(
                client = allas_client,
                bucket_name = allas_bucket,
                object_path = formatted_file_path 
            )
            files[file_name] = file_data
    return files 
# Created and works
def delete_folder_objects(
    file_lock: any,
    allas_client: any,
    allas_bucket: str,
    object: str,
    replacers: any
):
    with file_lock:
        object_path = set_object_path(
            object = object,
            replacers = replacers
        )

        folder_objects = get_object_list(
            client = allas_client,
            bucket_name = allas_bucket,
            path_prefix = object_path
        )

        for file_path in folder_objects.keys():
            if '.pkl' in file_path:
                pkl_split = file_path.split('.pkl')
                
                remove_object(
                    client = allas_client,
                    bucket_name = allas_bucket,
                    object_path = pkl_split[0]
                )
# Fixt the paths and abstract away object changes