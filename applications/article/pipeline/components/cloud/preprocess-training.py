from typing import NamedTuple
@component( 
    base_image = "python:3.10",
    packages_to_install = [
        "python-swiftclient",
        "mlflow~=2.12.2", 
        "boto3~=1.21.0",
        "numpy",
        "torch==2.4.0+cpu", 
        "torchvision==0.19.0+cpu",
        "torchmetrics"
    ],
    pip_index_urls=[
        "https://pypi.org/simple",
        "https://pypi.org/simple",
        "https://pypi.org/simple",
        "https://pypi.org/simple",
        "https://download.pytorch.org/whl/cpu",
        "https://download.pytorch.org/whl/cpu",
        "https://pypi.org/simple"
    ],
    output_component_file = 'components/preprocess_component.yaml',
)
def preprocess_train( 
    storage_parameters: dict,
    training_parameters: dict,
    mlflow_parameters: dict
) -> NamedTuple("Output", [('storage_uri', str), ('run_id', str),]):
    import logging
    from collections import namedtuple
    import swiftclient as sc
    import pickle

    import torch
    from torchvision import datasets
    import torchvision.transforms as T
    import torchmetrics as TM

    import time as t
    import pickle
    import os
    import mlflow
    import mlflow.pytorch
    
    import torch.nn as nn
    import torch.nn.functional as F

    import numpy as np
    import re

    # BOILERPLATE START

    def set_formatted_user(
        user: str   
    ) -> any:
        return re.sub(r'[^a-z0-9]+', '-', user)
    def general_object_metadata():
        general_object_metadata = {
            'version': 1
        }
        return general_object_metadata
    # Works
    def is_swift_client(
        storage_client: any
    ) -> any:
        return isinstance(storage_client, sc.Connection)
    # Works
    def swift_setup_client(
        pre_auth_url: str,
        pre_auth_token: str,
        user_domain_name: str,
        project_domain_name: str,
        project_name: str,
        auth_version: str
    ) -> any:
        swift_client = sc.Connection(
            preauthurl = pre_auth_url,
            preauthtoken = pre_auth_token,
            os_options = {
                'user_domain_name': user_domain_name,
                'project_domain_name': project_domain_name,
                'project_name': project_name
            },
            auth_version = auth_version
        )
        return swift_client
    # Works
    def swift_create_bucket(
        swift_client: any,
        bucket_name: str
    ) -> bool:
        try:
            swift_client.put_container(
                container = bucket_name
            )
            return True
        except Exception as e:
            return False
    # Works
    def swift_check_bucket(
        swift_client: any,
        bucket_name:str
    ) -> any:
        try:
            bucket_info = swift_client.get_container(
                container = bucket_name
            )
            bucket_metadata = bucket_info[0]
            list_of_objects = bucket_info[1]
            return {'metadata': bucket_metadata, 'objects': list_of_objects}
        except Exception as e:
            return {} 
    # Refactored
    def swift_delete_bucket(
        swift_client: any,
        bucket_name: str
    ) -> bool:
        try:
            swift_client.delete_container(
                container = bucket_name
            )
            return True
        except Exception as e:
            return False
    # Created and works
    def swift_list_buckets(
        swift_client: any
    ) -> any:
        try:
            account_buckets = swift_client.get_account()[1]
            return account_buckets
        except Exception as e:
            return {}
    # Works
    def swift_create_object(
        swift_client: any,
        bucket_name: str, 
        object_path: str, 
        object_data: any,
        object_metadata: any
    ) -> bool: 
        # This should be updated to handle 5 GB objects
        # It also should handle metadata
        try:
            swift_client.put_object(
                container = bucket_name,
                obj = object_path,
                contents = object_data,
                headers = object_metadata
            )
            return True
        except Exception as e:
            return False
    # Works
    def swift_check_object(
        swift_client: any,
        bucket_name: str, 
        object_path: str
    ) -> any: 
        try:
            object_metadata = swift_client.head_object(
                container = bucket_name,
                obj = object_path
            )       
            return object_metadata
        except Exception as e:
            return {} 
    # Refactored and works
    def swift_get_object(
        swift_client:any,
        bucket_name: str,
        object_path: str
    ) -> any:
        try:
            response = swift_client.get_object(
                container = bucket_name,
                obj = object_path 
            )
            object_info = response[0]
            object_data = response[1]
            return {'data': object_data, 'info': object_info}
        except Exception as e:
            return {}     
    # Refactored   
    def swift_remove_object(
        swift_client: any,
        bucket_name: str, 
        object_path: str
    ) -> bool: 
        try:
            swift_client.delete_object(
                container = bucket_name, 
                obj = object_path
            )
            return True
        except Exception as e:
            return False
    # Works
    def swift_update_object(
        swift_client: any,
        bucket_name: str, 
        object_path: str, 
        object_data: any,
        object_metadata: any
    ) -> bool:  
        remove = swift_remove_object(
            swift_client = swift_client, 
            bucket_name = bucket_name, 
            object_path = object_path
        )
        if not remove:
            return False
        create = swift_create_object(
            swift_client = swift_client, 
            bucket_name = bucket_name, 
            object_path = object_path, 
            object_data = object_data,
            object_metadata = object_metadata
        )
        return create
    # Works
    def swift_create_or_update_object(
        swift_client: any,
        bucket_name: str, 
        object_path: str, 
        object_data: any,
        object_metadata: any
    ) -> any:
        bucket_info = swift_check_bucket(
            swift_client = swift_client, 
            bucket_name = bucket_name
        )
        
        if len(bucket_info) == 0:
            creation_status = swift_create_bucket(
                swift_client = swift_client, 
                bucket_name = bucket_name
            )
            if not creation_status:
                return False
        
        object_info = swift_check_object(
            swift_client = swift_client, 
            bucket_name = bucket_name, 
            object_path = object_path
        )
        
        if len(object_info) == 0:
            return swift_create_object(
                swift_client = swift_client, 
                bucket_name = bucket_name, 
                object_path = object_path, 
                object_data = object_data,
                object_metadata = object_metadata
            )
        else:
            return swift_update_object(
                swift_client = swift_client, 
                bucket_name = bucket_name, 
                object_path = object_path, 
                object_data = object_data,
                object_metadata = object_metadata
            )

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
        storage_names.append(bucket_prefix + '-experiment-' + ice_id + '-' + set_formatted_user(user = user))
        return storage_names
    # created and works
    def setup_storage(
        storage_parameters: any
    ) -> any:
        storage_client = setup_storage_client(
            storage_parameters = storage_parameters
        ) 
        
        storage_name = set_bucket_names(
        storage_parameters = storage_parameters
        )
        
        return storage_client, storage_name
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
            'time': 'TIMES/name'
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
        #print('Used object path:' + str(object_path))
        return object_path
    # created and works
    def setup_storage(
        storage_parameters: any
    ) -> any:
        storage_client = setup_storage_client(
            storage_parameters = storage_parameters
        ) 
        
        storage_name = set_bucket_names(
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

    def gather_time(
        storage_client: any,
        storage_name: any,
        time_group: any,
        time_name: any,
        start_time: int,
        end_time: int
    ):
        time_object = get_object(
            storage_client = storage_client,
            bucket_name = storage_name,
            object_name = 'time',
            path_replacers = {
                'name': time_group
            },
            path_names = []
        )

        time_data = {}
        time_metadata = {} 
        if time_object is None:
            time_data = {}
            time_metadata = general_object_metadata()
        else:
            time_data = time_object['data']
            time_metadata = time_object['custom-meta']
        
        current_key_amount = len(time_data)
        current_key_full = False
        current_key = str(current_key_amount)
        if 0 < current_key_amount:
            time_object = time_data[current_key]
            if 0 < time_object['total-seconds']:
                current_key_full = True
        
        changed = False
        if 0 < end_time and 0 < current_key_amount and not current_key_full:
            stored_start_time = time_data[current_key]['start-time']
            time_diff = (end_time-stored_start_time)
            time_data[current_key]['end-time'] = end_time
            time_data[current_key]['total-seconds'] = round(time_diff,5)
            changed = True
        else:
            next_key_amount = len(time_data) + 1
            new_key = str(next_key_amount)
        
            if 0 < start_time and 0 == end_time:
                time_data[new_key] = {
                    'name': time_name,
                    'start-time': start_time,
                    'end-time': 0,
                    'total-seconds': 0
                }
                changed = True

            if 0 < start_time and 0 < end_time:
                time_diff = (end_time-start_time)
                time_data[new_key] = {
                    'name': time_name,
                    'start-time': start_time,
                    'end-time': end_time,
                    'total-seconds': round(time_diff,5)
                }
                changed = True

        if changed:
            time_metadata['version'] = time_metadata['version'] + 1
            set_object(
                storage_client = storage_client,
                bucket_name = storage_name,
                object_name = 'time',
                path_replacers = {
                    'name': time_group
                },
                path_names = [],
                overwrite = True,
                object_data = time_data,
                object_metadata = time_metadata 
            )

    
    class CNNClassifier(nn.Module):
        def __init__(self):
            super().__init__()
            self.conv1 = nn.Conv2d(1, 6, 5)
            self.pool = nn.MaxPool2d(2, 2)
            self.conv2 = nn.Conv2d(6, 16, 5)
            self.fc1 = nn.Linear(16 * 4 * 4, 120)
            self.fc2 = nn.Linear(120, 84)
            self.fc3 = nn.Linear(84, 10)

        def forward(self, x):
            x = self.pool(F.relu(self.conv1(x)))
            x = self.pool(F.relu(self.conv2(x)))
            x = x.view(-1, 16 * 4 * 4)
            x = F.relu(self.fc1(x))
            x = F.relu(self.fc2(x))
            x = self.fc3(x)
            return x
        
    def get_general_metrics():
        general_metrics = TM.MetricCollection([
            TM.classification.MulticlassAccuracy(
                num_classes = 10,
                average = 'macro'
            ),
            TM.classification.MulticlassPrecision(
                num_classes = 10,
                average = 'macro'
            ),
            TM.classification.MulticlassRecall(
                num_classes = 10,
                average = 'macro'
            )
        ])
        return general_metrics
        
    def get_class_metrics():
        class_metrics = TM.MetricCollection([
            TM.classification.MulticlassAccuracy(
                num_classes = 10,
                average = None
            ),
            TM.classification.MulticlassPrecision(
                num_classes = 10,
                average = None
            ),
            TM.classification.MulticlassRecall(
                num_classes = 10,
                average = None
            )
        ])
        return class_metrics

    def parse_torchmetrics(
        metrics: any,
        labels: any
    ):
        collected_metrics = {}
        for key,value in metrics.items():
            if key == 'name':
                continue
            if 'class-' in key:
                image_labels = {
                    0: 'top',
                    1: 'trouser',
                    2: 'pullover',
                    3: 'dress',
                    4: 'coat',
                    5: 'sandal',
                    6: 'shirt',
                    7: 'sneaker',
                    8: 'bag',
                    9: 'ankle-boot',
                }
                #logger.info('')
                i = 0
                for class_value in value:
                    formatted_key = key.replace('class', labels[i])
                    rounded_value = round(class_value,5)
                    #logger.info(str(formatted_key) + '=' + str(rounded_value))
                    collected_metrics[formatted_key] = rounded_value
                    i += 1
                continue
            rounded_value = round(value,5)
            #logger.info(str(key) + '=' + str(rounded_value))
            collected_metrics[key] = rounded_value
        return collected_metrics

    def setup_mlflow(
        logger: any,
        mlflow_parameters: any
    ):
        mlflow_s3_endpoint_url = mlflow_parameters['s3-endpoint-url']
        mlflow_tracking_uri = mlflow_parameters['tracking-uri']
        mlflow_experiment_name = mlflow_parameters['experiment-name']
        
        os.environ['MLFLOW_S3_ENDPOINT_URL'] = mlflow_s3_endpoint_url

        logger.info(f"Using MLflow tracking URI: {mlflow_tracking_uri}")
        mlflow.set_tracking_uri(mlflow_tracking_uri)
        logger.info(f"Using MLflow experiment: {mlflow_experiment_name}")
        mlflow.set_experiment(mlflow_experiment_name)
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    component_time_start = t.time()

    storage_client, storage_names = setup_storage(
        storage_parameters = storage_parameters
    )

    logger.info('Storage setup')

    output = namedtuple('Output', ['storage_uri', 'run_id'])
    
    train_batch_size = training_parameters['hp-train-batch-size']
    test_batch_size = training_parameters['hp-test-batch-size']
    
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

    setup_mlflow(
        logger = logger,
        mlflow_parameters = mlflow_parameters
    )

    logger.info('MLflow setup') 

    learning_rate = training_parameters['hp-learning-rate']
    momentum = training_parameters['hp-momentum']
    seed = training_parameters['hp-seed']
    epochs = training_parameters['hp-epochs']
    train_print_rate = training_parameters['train-print-rate']

    with mlflow.start_run() as run:
        time_start = t.time()

        run_id = run.info.run_id
        logger.info(f"Run ID: {run_id}")
        
        logger.info("Model parameters logged")
        for key,value in training_parameters.items():
            if 'hp-' in key:
                mlflow.log_param(key, value)
        
        logger.info('Defining model')
        
        model = CNNClassifier()
        criterion = torch.nn.CrossEntropyLoss()
        optimizer = torch.optim.SGD(
            model.parameters(), 
            lr = learning_rate, 
            momentum = momentum
        )
        torch.manual_seed(seed)

        logger.info('Defining metrics')
        general_metrics = get_general_metrics()
        class_metrics = get_class_metrics()
        
        logger.info('Starting model training')
        current_epoch = 0
        for epoch in range(epochs):
            running_loss = 0.0
            model.train()
            for i, data in enumerate(train_loader):
                inputs, labels = data
                optimizer.zero_grad()
                outputs = model(inputs)
                
                loss = criterion(outputs, labels)
                
                loss.backward()
                optimizer.step()
                running_loss += loss.item()

                preds = torch.max(outputs, 1)[1]
        
                general_metrics(preds, labels)
                
                if (i + 1) % train_print_rate == 0:
                    avg_loss = running_loss / train_print_rate
                    train_general_metrics = general_metrics.compute()
                    acc = round(train_general_metrics['MulticlassAccuracy'].item(),3)
                    pre = round(train_general_metrics['MulticlassPrecision'].item(),3)
                    rec = round(train_general_metrics['MulticlassRecall'].item(),3)
                    general_metrics.reset()
                    logger.info(f'Epoch: {epoch + 1}/{epochs}, Batch {i + 1}, Loss: {avg_loss}, Accuracy: {acc}, Precision: {pre}, Recall: {rec}')
                    running_loss = 0.0
            current_epoch += 1
        logger.info('Training complete')
        
        general_metrics.reset()
        
        logger.info('Starting model testing')
        running_loss = 0.0
        predictions = []
        with torch.no_grad():
            model.eval()
            for i, data in enumerate(test_loader):
                inputs, labels = data
                outputs = model(inputs)
                preds = torch.max(outputs, 1)[1]
                loss = criterion(outputs, labels)
                general_metrics(preds, labels)
                class_metrics(preds, labels)
                predictions.extend(preds.tolist())
                running_loss += loss.item()
        logger.info('Testing complete')
        
        test_general_metrics = general_metrics.compute()
        test_class_metrics = class_metrics.compute()

        general_metrics.reset()
        class_metrics.reset()

        logger.info('Logging model')
        model_name = mlflow_parameters['model-name']
        registered_name = mlflow_parameters['registered-name']
        mlflow.pytorch.log_model(
            model,
            model_name,
            registered_model_name = registered_name
        )

        logger.info('Logging predictions')
        np.save("predictions.npy", predictions)
        mlflow.log_artifact(
            local_path = "predictions.npy",
            artifact_path = "predicted_qualities/"
        )

        logger.info("Storing predictions")
        set_object(
            storage_client = storage_client,
            bucket_name = storage_names[-1],
            object_name = 'artifacts',
            path_replacers = {
                'name': 'LOCAL'
            },
            path_names = [
                'predictions'
            ],
            overwrite = True,
            object_data = predictions,
            object_metadata = general_object_metadata()
        )

        logger.info('Formatting model')
        
        model_parameters = model.state_dict()
        optimizer_parameters = optimizer.state_dict()

        parameters = {
            'epoch': current_epoch,
            'model': model_parameters,
            'optimizer': optimizer_parameters
        }

        logger.info("Storing parameters")
        set_object(
            storage_client = storage_client,
            bucket_name = storage_names[-1],
            object_name = 'artifacts',
            path_replacers = {
                'name': 'LOCAL'
            },
            path_names = [
                'parameters'
            ],
            overwrite = True,
            object_data = parameters,
            object_metadata = general_object_metadata()
        )

        logger.info('Formatting metrics')
        
        accuracy = test_general_metrics['MulticlassAccuracy'].item()
        precision = test_general_metrics['MulticlassPrecision'].item()
        recall = test_general_metrics['MulticlassRecall'].item()

        class_accuracy = test_class_metrics['MulticlassAccuracy'].tolist()
        class_precision = test_class_metrics['MulticlassPrecision'].tolist()
        class_recall = test_class_metrics['MulticlassRecall'].tolist()

        performance = {
            'name': 'Convolutional-neural-network-classifier',
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'class-accuracy': class_accuracy,
            'class-precision': class_precision,
            'class-recall': class_recall
        }

        parsed_performance = parse_torchmetrics(
            metrics = performance,
            labels = {
                0: 'top',
                1: 'trouser',
                2: 'pullover',
                3: 'dress',
                4: 'coat',
                5: 'sandal',
                6: 'shirt',
                7: 'sneaker',
                8: 'bag',
                9: 'ankle-boot',
            }
        )
 
        for key,value in parsed_performance.items():
            if 'name' in key:
                continue
            mlflow.log_metric(key, value)
        logger.info("Performance logged")

        logger.info('Formatting used time')
        
        time_end = t.time()
        time_diff = (time_end - time_start) 

        time = {
            'name': 'cloud-model-training',
            'start-time': time_start,
            'end-time': time_end,
            'total-seconds': round(time_diff,5)
        }

        for key,value in time.items():
            if 'name' in key:
                continue
            if 'time' in key:
                continue
            mlflow.log_metric(key, value)
        logger.info("Time logged")

        metrics = {
            'performance': performance,
            'time': time
        }

        logger.info("Storing metrics")
        set_object(
            storage_client = storage_client,
            bucket_name = storage_names[-1],
            object_name = 'artifacts',
            path_replacers = {
                'name': 'LOCAL'
            },
            path_names = [
                'metrics'
            ],
            overwrite = True,
            object_data = metrics,
            object_metadata = general_object_metadata()
        )

        component_time_end = t.time()

        logger.info("Storing time")
        gather_time( 
            storage_client = storage_client,
            storage_name = storage_names[-1],
            time_group = 'cloud-exp',
            time_name = 'preprocess-train',
            start_time = component_time_start,
            end_time = component_time_end
        )

        return output(mlflow.get_artifact_uri(), run_id)