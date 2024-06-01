import pickle
import swiftclient as sc
# Created
def setup_client(
    parameters: any
) -> any:
    allas_client = sc.Connection(
        preauthurl = parameters['pre_auth_url'],
        preauthtoken = parameters['pre_auth_token'],
        os_options = {
            'user_domain_name': parameters['user_domain_name'],
            'project_domain_name': parameters['project_domain_name'],
            'project_name': parameters['project_name']
        }
    )
    return allas_client

def create_bucket(
    client: any,
    bucket_name: str
) -> bool:
    try:
        client.put_container(
            container = bucket_name
        )
        return True
    except Exception as e:
        return False

def check_bucket(
    client: any,
    bucket_name:str
) -> bool:
    try:
        container_info = client.get_container(
            container = bucket_name
        )
        return container_info
    except Exception as e:
        return None 
    
def delete_bucket(
    client: any,
    bucket_name:str
) -> bool:
    try:
        client.delete_container(
            container = bucket_name
        )
        return True
    except Exception as e:
        return False

def create_object(
    client: any,
    bucket_name: str, 
    object_path: str, 
    data: any
) -> bool: 
    try:
        client.put_object(
            container = bucket_name,
            obj = object_path + '.pkl',
            contents = pickle.dumps(data),
            content_type = 'application/pickle'
        )
        return True
    except Exception as e:
        return False
    
def check_object(
    client: any,
    bucket_name: str, 
    object_path: str
) -> any: 
    try:
        object_info = client.head_object(
            container = bucket_name,
            obj = object_path + '.pkl'
        )       
        return object_info
    except Exception as e:
        return {} 

def get_object(
    client:any,
    bucket_name: str,
    object_path: str
) -> any:
    try:
        content = client.get_object(
            container = bucket_name,
            obj = object_path + '.pkl' 
        )
        data = pickle.loads(content[1])
        return data
    except Exception as e:
        return None     
    
def remove_object(
    client: any,
    bucket_name: str, 
    object_path: str
) -> bool: 
    try:
        client.delete_object(
            container = bucket_name, 
            obj = object_path + '.pkl'
        )
        return True
    except Exception as e:
        return False

def update_object(
    client: any,
    bucket_name: str, 
    object_path: str, 
    data: any,
) -> bool:  
    remove = remove_object(
        client, 
        bucket_name, 
        object_path
    )
    if remove:
        create = create_object(
            client, 
            bucket_name, 
            object_path, 
            data
        )
        if create:
            return True
    return False

def check_or_create_object(
    client: any,
    bucket_name: str,
    object_path: str,
    data: any
) -> any:
    object_status = check_object(
        client,
        bucket_name,
        object_path
    )
    if object_status:
        return True
    return create_object(
        client, 
        bucket_name, 
        object_path, 
        data
    )

def create_or_update_object(
    client: any,
    bucket_name: str, 
    object_path: str, 
    data: any
) -> any:
    bucket_status = check_bucket(
        client, 
        bucket_name
    )
    
    if not bucket_status:
        creation_status = create_bucket(
            client, 
            bucket_name
        )
        if not creation_status:
            return False
    
    object_status = check_object(
        client, 
        bucket_name, 
        object_path
    )
    
    if not object_status:
        return create_object(
            client, 
            bucket_name, 
            object_path, 
            data
        )
    else:
        return update_object(
            client, 
            bucket_name, 
            object_path, 
            data
        )

def get_object_list(
    client: any,
    bucket_name: str,
    path_prefix: str
) -> dict:
    try:
        objects = client.get_container(container = bucket_name)[1]
        object_dict = {}
        for object in objects:
            metadata = {
                'hash': object['hash'],
                'bytes': object['bytes'],
                'last_modified': object['last_modified']
            }
            if path_prefix in object['name']:
                object_dict[object['name']] = metadata
        return object_dict
    except Exception as e:
        return None  
    
def remove_objects(
    client: any,
    bucket_name: str,
    path_prefix: str
):
    # empty path prefix means 
    # that all objects in the 
    # container are deleted
    objects = get_object_list(client, bucket_name, path_prefix)
    for object_name in objects.keys():
        pkl_split = object_name.split('.')[0]
        remove_object(client, bucket_name, pkl_split)