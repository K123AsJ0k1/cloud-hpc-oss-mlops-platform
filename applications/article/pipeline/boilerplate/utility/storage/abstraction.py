# 3-2-2

# Refactored and Works
def set_encoded_metadata(
    used_client: str,
    object_metadata: any
) -> any:
    encoded_metadata = {}
    if used_client == 'swift':
        key_initial = 'x-object-meta'
        for key, value in object_metadata.items():
            encoded_key = key_initial + '-' + key
            if isinstance(value, list):
                encoded_metadata[encoded_key] = 'list=' + ','.join(map(str, value))
                continue
            encoded_metadata[encoded_key] = str(value)
    return encoded_metadata
# Refactored and works
def get_general_metadata(
    used_client: str,
    object_metadata: any
) -> any:
    general_metadata = {}
    if used_client == 'swift':
        key_initial = 'x-object-meta'
        for key, value in object_metadata.items():
            if not key_initial == key[:len(key_initial)]:
                general_metadata[key] = value
    return general_metadata
# Refactored and works
def get_decoded_metadata(
    used_client: str,
    object_metadata: any
) -> any: 
    decoded_metadata = {}
    if used_client == 'swift':
        key_initial = 'x-object-meta'
        for key, value in object_metadata.items():
            if key_initial == key[:len(key_initial)]:
                decoded_key = key[len(key_initial) + 1:]
                if 'list=' in value:
                    string_integers = value.split('=')[1]
                    values = string_integers.split(',')
                    if len(values) == 1 and values[0] == '':
                        decoded_metadata[decoded_key] = []
                    else:
                        try:
                            decoded_metadata[decoded_key] = list(map(int, values))
                        except:
                            decoded_metadata[decoded_key] = list(map(str, values))
                    continue
                if value.isnumeric():
                    decoded_metadata[decoded_key] = int(value)
                    continue
                decoded_metadata[decoded_key] = value
    return decoded_metadata
# Refactored and works
def set_bucket_names(
    storage_parameters: any
) -> any:
    storage_names = []
    bucket_prefix = storage_parameters['bucket-prefix']
    ice_id = storage_parameters['ice-id']
    user = storage_parameters['user']
    storage_names.append(bucket_prefix + '-forwarder-' + ice_id)
    storage_names.append(bucket_prefix + '-submitter-' + ice_id + '-' + set_formatted_user(user = user))
    storage_names.append(bucket_prefix + '-pipeline-' + ice_id + '-' + set_formatted_user(user = user))
    return storage_names
# Refactored and works
def setup_storage_client(
    storage_parameters: any
) -> any:
    storage_client = None
    if storage_parameters['used-client'] == 'swift':
        storage_client = swift_setup_client(
            pre_auth_url = storage_parameters['pre-auth-url'],
            pre_auth_token = storage_parameters['pre-auth-token'],
            user_domain_name = storage_parameters['user-domain-name'],
            project_domain_name = storage_parameters['project-domain-name'],
            project_name = storage_parameters['project-name'],
            auth_version = storage_parameters['auth-version']
        )
    return storage_client
# Refactored and works
def check_object_metadata(
    storage_client: any,
    bucket_name: str, 
    object_path: str
) -> any: 
    object_metadata = {
        'general-meta': {},
        'custom-meta': {}
    }
    if is_swift_client(storage_client = storage_client):
        all_metadata = swift_check_object(
           swift_client = storage_client,
           bucket_name = bucket_name,
           object_path = object_path
        ) 

        general_metadata = {}
        custom_metadata = {}
        if not len(all_metadata) == 0:
            general_metadata = get_general_metadata(
                used_client = 'swift',
                object_metadata = all_metadata
            )
            custom_metadata = get_decoded_metadata(
                used_client = 'swift',
                object_metadata = all_metadata
            )

        object_metadata['general-meta'] = general_metadata
        object_metadata['custom-meta'] = custom_metadata

    return object_metadata
# Refactored and works
def get_object_content(
    storage_client: any,
    bucket_name: str,
    object_path: str
) -> any:
    object_content = {}
    if is_swift_client(storage_client = storage_client):
        fetched_object = swift_get_object(
            swift_client = storage_client,
            bucket_name = bucket_name,
            object_path = object_path
        )
        object_content['data'] = pickle.loads(fetched_object['data'])
        object_content['general-meta'] = get_general_metadata(
            used_client = 'swift',
            object_metadata = fetched_object['info']
        )
        object_content['custom-meta'] = get_decoded_metadata(
            used_client = 'swift',
            object_metadata = fetched_object['info']
        )
    return object_content
# Refactored    
def remove_object(
    storage_client: any,
    bucket_name: str, 
    object_path: str
) -> bool: 
    removed = False
    if is_swift_client(storage_client = storage_client):
        removed = swift_remove_object(
            swift_client = storage_client,
            bucket_name = bucket_name,
            object_path = object_path
        )
    return removed
# Refactored and works
def create_or_update_object(
    storage_client: any,
    bucket_name: str, 
    object_path: str, 
    object_data: any,
    object_metadata: any
) -> any:
    success = False
    if is_swift_client(storage_client = storage_client):
        formatted_data = pickle.dumps(object_data)
        formatted_metadata = set_encoded_metadata(
            used_client = 'swift',
            object_metadata = object_metadata
        )

        success = swift_create_or_update_object(
            swift_client = storage_client,
            bucket_name = bucket_name,
            object_path = object_path,
            object_data = formatted_data,
            object_metadata = formatted_metadata
        )
    return success
# Created and works
def format_bucket_metadata(
    used_client: str,
    bucket_metadata: any
) -> any:
    formatted_metadata = {}
    if used_client == 'swift':
        relevant_values = {
            'x-container-object-count': 'object-count',
            'x-container-bytes-used-actual': 'used-bytes',
            'last-modified': 'date',
            'content-type': 'type'
        }
        formatted_metadata = {}
        for key,value in bucket_metadata.items():
            if key in relevant_values:
                formatted_key = relevant_values[key]
                formatted_metadata[formatted_key] = value
    return formatted_metadata
# Created and works
def format_bucket_objects(
    used_client: str,
    bucket_objects: any
) -> any:
    formatted_objects = {}
    if used_client == 'swift':
        for bucket_object in bucket_objects:
            formatted_object_metadata = {
                'hash': 'id',
                'bytes': 'used-bytes',
                'last_modified': 'date'
            }
            object_key = None
            object_metadata = {}
            for key, value in bucket_object.items():
                if key == 'name':
                    object_key = value
                if key in formatted_object_metadata:
                    formatted_key = formatted_object_metadata[key]
                    object_metadata[formatted_key] = value
            formatted_objects[object_key] = object_metadata
    return formatted_objects
# Created and works
def format_bucket_info(
    used_client: str,
    bucket_info: any
) -> any:
    bucket_metadata = {}
    bucket_objects = {}
    if used_client == 'swift':
        bucket_metadata = format_bucket_metadata(
            used_client = used_client,
            bucket_metadata = bucket_info['metadata']
        )
        bucket_objects = format_bucket_objects(
            used_client = used_client,
            bucket_objects = bucket_info['objects']
        )
    return {'metadata': bucket_metadata, 'objects': bucket_objects} 
# Created and works
def get_bucket_info(
    storage_client: any,
    bucket_name: str
) -> any:
    bucket_info = {}
    if is_swift_client(storage_client = storage_client):
        unformatted_bucket_info = swift_check_bucket(
            swift_client = storage_client,
            bucket_name = bucket_name
        )
        bucket_info = format_bucket_info(
            used_client = 'swift',
            bucket_info = unformatted_bucket_info
        )
    return bucket_info
# Created and works
def format_container_info(
    used_client: str,
    container_info: any
) -> any:
    formatted_container_info = {}
    if used_client == 'swift':
        for bucket in container_info:
            bucket_name = bucket['name']
            bucket_count = bucket['count']
            bucket_size = bucket['bytes']
            formatted_container_info[bucket_name] = {
                'amount': bucket_count,
                'size': bucket_size
            }
    return formatted_container_info
# Created and works
def get_container_info( 
    storage_client: any
) -> any:
    container_info = {}
    if is_swift_client(storage_client = storage_client):
        unformatted_container_info = swift_list_buckets(
            swift_client = storage_client 
        )
        container_info = format_container_info(
            used_client = 'swift',
            container_info = unformatted_container_info
        )
    return container_info