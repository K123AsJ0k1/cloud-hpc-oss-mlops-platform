@component( 
    base_image = "python:3.10",
    packages_to_install = [
        "python-swiftclient",
        "torch==2.3.0", 
        "torchvision==0.18.0"
    ],
    pip_index_urls=[
        "https://pypi.org/simple",
        "https://download.pytorch.org/whl/cpu",
        "https://download.pytorch.org/whl/cpu"
    ],
    output_component_file = 'components/preprocess_component.yaml',
)
def preprocess( 
    allas_parameters: dict,
    ray_parameters: dict,
    metadata_parameters: dict
) -> bool:
    import time as t
    
    import logging
    import swiftclient as sc
    import pickle
    
    import torch
    from torchvision import datasets
    import torchvision.transforms as T

    ''' START OF FUNCTIONS '''
    
    '''ALLAS'''
    
    def setup_allas(
        parameters: any
    ) -> any:
        allas_client = sc.Connection(
            preauthurl = parameters['pre_auth_url'],
            preauthtoken = parameters['pre_auth_token'],
            os_options = {
                'user_domain_name': parameters['user_domain_name'],
                'project_domain_name': parameters['project_domain_name'],
                'project_name': parameters['project_name']
            },
            auth_version = parameters['auth_version']
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


    '''GATHER'''

    def gather_time(
        logger: any,
        allas_client: any,
        allas_bucket: str,
        kubeflow_user: str,
        time_folder_path: str,
        object_name: str,
        action_name: str,
        start_time: int,
        end_time: int
    ):
        time_path = time_folder_path + '/' + object_name
        logger.info('Time object path:' + str(time_path))
        current_data = get_object(
            client = allas_client,
            bucket_name = allas_bucket,
            object_path = time_path
        )

        object_data = None
        if current_data is None:
            object_data = {}
        else:
            object_data = current_data

        if not kubeflow_user in object_data:
            object_data[kubeflow_user] = {}

        user_time_dict = object_data[kubeflow_user]

        current_key_amount = len(user_time_dict)
        current_key_full = False
        current_key = str(current_key_amount)
        if 0 < current_key_amount:
            time_object = user_time_dict[current_key]
            if 0 < time_object['total-seconds']:
                current_key_full = True
        
        changed = False
        if 0 < end_time and 0 < current_key_amount and not current_key_full:
            stored_start_time = user_time_dict[current_key]['start-time']
            time_diff = (end_time-stored_start_time)
            user_time_dict[current_key]['end-time'] = end_time
            user_time_dict[current_key]['total-seconds'] = round(time_diff,5)
            changed = True
        else:
            next_key_amount = len(user_time_dict) + 1
            new_key = str(next_key_amount)
        
            if 0 < start_time and 0 == end_time:
                user_time_dict[new_key] = {
                    'name': action_name,
                    'start-time': start_time ,
                    'end-time': 0,
                    'total-seconds': 0
                }
                changed = True

            if 0 < start_time and 0 < end_time:
                time_diff = (end_time-start_time)
                user_time_dict[new_key] = {
                    'name': action_name,
                    'start-time': start_time,
                    'end-time': end_time,
                    'total-seconds': round(time_diff,5)
                }
                changed = True

        if changed:
            object_data[kubeflow_user] = user_time_dict
            create_or_update_object(
                client = allas_client,
                bucket_name = allas_bucket,
                object_path = time_path, 
                data = object_data
            )    

    ''' END OF FUNCTIONS '''

    time_start = t.time()

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    allas_client = setup_allas(
        parameters = allas_parameters
    )
    allas_bucket = allas_parameters['allas-bucket'] 
    job_parameters = ray_parameters['job-parameters']
    data_folder_path = job_parameters['data-folder-path']
    train_batch_size = job_parameters['hp-train-batch-size']
    test_batch_size = job_parameters['hp-test-batch-size']
    kubeflow_user = metadata_parameters['kubeflow-user']
    time_folder_path = metadata_parameters['time-folder-path']

    train_loader_path = data_folder_path + '/fmnist-train'
    logger.info('Train loader path:' + str(train_loader_path))
    
    train_loader_metadata = check_object(
        client = allas_client,
        bucket_name = allas_bucket,
        object_path = train_loader_path
    )

    if len(train_loader_metadata) == 0:
        logger.info('Preprocessing train')
        
        train_transform = T.Compose([
            T.ToTensor(),
            T.Normalize((0.5,), (0.5,))
        ])

        train_data = datasets.FashionMNIST(
            root = './data', 
            train = True, 
            download = True, 
            transform = train_transform
        )
        
        train_loader = torch.utils.data.DataLoader(
            train_data, 
            batch_size = train_batch_size, 
            shuffle = True
        )

        train_loader_status = create_or_update_object(
            client = allas_client,
            bucket_name = allas_bucket,
            object_path = train_loader_path,
            data = train_loader
        )
        logger.info('Train loader stored:' + str(train_loader_status))

        if not train_loader_status:
            return False

    test_loader_path = data_folder_path + '/fmnist-test'
    logger.info('Test loader path:' + str(test_loader_path))

    test_loader_metadata = check_object(
        client = allas_client,
        bucket_name = allas_bucket,
        object_path = test_loader_path
    )

    if len(test_loader_metadata) == 0:
        logger.info('Preprocessing test')
        test_transform = T.Compose([
            T.ToTensor(),
            T.Normalize((0.5,), (0.5,))
        ])

        test_data = datasets.FashionMNIST(
            root = './data', 
            train = False, 
            download = True, 
            transform = test_transform
        )

        test_loader = torch.utils.data.DataLoader(
            test_data, 
            batch_size = test_batch_size, 
            shuffle = False
        )

        test_loader_status = create_or_update_object(
            client = allas_client,
            bucket_name = allas_bucket,
            object_path = test_loader_path,
            data = test_loader
        )
        logger.info('Test loader stored:' + str(test_loader_status))

        if not test_loader_status:
            return False
        
    time_end = t.time()
    
    gather_time(
        logger = logger,
        allas_client = allas_client,
        allas_bucket =  allas_bucket,
        kubeflow_user = kubeflow_user,
        time_folder_path = time_folder_path,
        object_name = 'components',
        action_name = 'integration-preprocessing',
        start_time = time_start,
        end_time = time_end
    )

    gather_time(
        logger = logger,
        allas_client = allas_client,
        allas_bucket =  allas_bucket,
        kubeflow_user = kubeflow_user,
        time_folder_path = time_folder_path,
        object_name = 'workflow',
        action_name = 'integration-pipeline',
        start_time = time_start,
        end_time = 0
    )

    logger.info('Preprocess complete')

    return True