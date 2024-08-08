# Refactored
def set_code(
    storage_client: any,
    storage_name: str,
    file_path: str,
    overwrite: bool
):
    file_data = None
    print('User code storage:' + str(storage_name))
    print('Used code path:' + str(file_path))
    with open(file_path, 'r') as f:
        file_data = f.read()

    path_split = file_path.split('/')
    directory_name = path_split[-2]
    file_name = path_split[-1]
    
    set_object(
        storage_client = storage_client,
        bucket_name = storage_name,
        object_name = directory_name,
        path_replacers = {
            'name': file_name
        },
        path_names = [],
        overwrite = overwrite,
        object_data = file_data,
        object_metadata = general_object_metadata()
    )
# Refactored
def get_code(
    storage_client: any,
    storage_name: str,
    code_type: str,
    code_file: str
) -> any:
    print('User code storage:' + str(storage_name))
    fetched_object = get_object(
        storage_client = storage_client,
        bucket_name = storage_name,
        object_name = code_type,
        path_replacers = {
            'name': code_file
        },
        path_names = []
    )
    code_object = {
        'data': fetched_object['data'],
        'metadata': fetched_object['custom-meta']
    }
    return code_object