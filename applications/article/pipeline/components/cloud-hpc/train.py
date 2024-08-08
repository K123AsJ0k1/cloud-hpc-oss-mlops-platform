from typing import NamedTuple

@component(
    base_image = "python:3.10",
    packages_to_install = [
        "python-swiftclient",
        "ray[default]",
        "mlflow~=2.12.2", 
        "boto3~=1.21.0",
        "numpy",
        "torch==2.4.0+cpu" 
    ],
    pip_index_urls=[
        "https://pypi.org/simple",
        "https://pypi.org/simple",
        "https://pypi.org/simple",
        "https://pypi.org/simple",
        "https://pypi.org/simple",
        "https://download.pytorch.org/whl/cpu"
    ],
    output_component_file = 'components/train_component.yaml',
) 
def train(   
    storage_parameters: dict,
    integration_parameters: dict,
    mlflow_parameters: dict
) -> NamedTuple("Output", [('storage_uri', str), ('run_id', str),]):
    
    import logging
    from collections import namedtuple
    
    import swiftclient as sc
    import pickle
    # saved_model: Output[Model
    import requests
    import json
    
    from datetime import datetime
    import time as t
        
    import os
    import mlflow
    import mlflow.pytorch
    
    from ray.job_submission import JobSubmissionClient
    from ray.job_submission import JobStatus

    import torch
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

    def set_route(
        route_type: str,
        route_name: str,
        path_replacers: any,
        path_names: any
    ): 
        # Check job-run and job-cancel
        routes = {
            'root': 'TYPE:/name',
            'logs': 'GET:/general/logs/name',
            'structure': 'GET:/general/structure',
            'setup': 'POST:/setup/config',
            'start': 'POST:/setup/start',
            'stop': 'POST:/setup/stop',
            'job-submit': 'POST:/requests/submit/job',
            'job-run': 'PUT:/requests/run/job/name',
            'job-cancel': 'PUT:/requests/cancel/job/name',
            'forwarding-submit': 'POST:/requests/submit/forwarding',
            'forwarding-cancel': 'PUT:/requests/cancel/type/user/key',
            'task-request': 'PUT:/tasks/request/signature',
            'task-result': 'GET:/tasks/result/id',
            'job-artifact': 'GET:/artifacts/job/type/name',
            'forwarding-artifact': 'GET:/artifacts/forwarding/type/user/key'
        }

        route = None
        if route_name in routes:
            i = 0
            route = routes[route_name].split('/')
            for name in route:
                if name in path_replacers:
                    replacer = path_replacers[name]
                    if 0 < len(replacer):
                        route[i] = replacer
                i = i + 1

            if not len(path_names) == 0:
                route.extend(path_names)

            if not len(route_type) == 0:
                route[0] = route_type + ':'
            
            route = '/'.join(route)
        #print('Used route: ' + str(route))
        return route
    # Created and works
    def get_response(
        route_type: str,
        route_url: str,
        route_input: any
    ) -> any:
        route_response = None
        if route_type == 'POST':
            route_response = requests.post(
                url = route_url,
                json = route_input
            )
        if route_type == 'PUT':
            route_response = requests.put(
                url = route_url
            )
        if route_type == 'GET':
            route_response = requests.get(
                url = route_url
            )
        return route_response
    # Created and works
    def set_full_url(
        address: str,
        port: str,
        used_route: str
    ) -> str:
        url_prefix = 'http://' + address + ':' + port
        route_split = used_route.split(':')
        url_type = route_split[0]
        used_path = route_split[1]
        full_url = url_prefix + used_path
        return url_type, full_url
    # Created and works
    def request_route(
        address: str,
        port: str,
        route_type: str,
        route_name: str,
        path_replacers: any,
        path_names: any,
        route_input: any,
        timeout: any
    ) -> any:
        used_route = set_route(
            route_type = route_type,
            route_name = route_name,
            path_replacers = path_replacers,
            path_names = path_names
        )

        url_type, full_url = set_full_url(
            address = address,
            port = port,
            used_route = used_route
        )
        
        route_response = get_response(
            route_type = url_type,
            route_url = full_url,
            route_input = route_input
        )

        route_status_code = None
        route_returned_text = {}
        if not route_response is None:
            route_status_code = route_response.status_code
            if route_status_code == 200:
                route_text = json.loads(route_response.text)

                if 'id' in route_text: 
                    task_result_route = set_route(
                        route_type = '',
                        route_name = 'task-result',
                        path_replacers = {
                            'id': route_text['id']
                        },
                        path_names = []
                    )

                    task_url_type, task_full_url = set_full_url(
                        address = address,
                        port = port,
                        used_route = task_result_route
                    )

                    start = t.time()
                    while t.time() - start <= timeout:
                        task_route_response = get_response(
                            route_type = task_url_type,
                            route_url = task_full_url,
                            route_input = {}
                        )
                        
                        task_status_code = route_response.status_code
                            
                        if task_status_code == 200:
                            task_text = json.loads(task_route_response.text)
                            if task_text['status'] == 'FAILED':
                                break
                            
                            if task_text['status'] == 'SUCCESS':
                                route_returned_text = task_text['result']
                                break
                        else:
                            break
                else:
                    route_returned_text = route_text
        return route_status_code, route_returned_text
    
    def start_forwarder_scheduler(
        address: str,
        port: str,
        scheduler_request: any
    ) -> bool:
        scheduler_route_code, scheduler_route_text = request_route(
            address = address,
            port = port,
            route_type = '',
            route_name = 'start',
            path_replacers = {},
            path_names = [],
            route_input = scheduler_request,
            timeout = 120
        )
        configured = False
        if scheduler_route_code == 200 and scheduler_route_text:
            configured = True
        return configured
    # Created
    def start_forwarder(
        address: str,
        port: str,
        configuration: any,
        scheduler_request: any
    ) -> bool:
        forwarder_route_code, forwarder_route_text  = request_route(
            address = address,
            port = port,
            route_type = '',
            route_name = 'setup',
            path_replacers = {},
            path_names = [],
            route_input = configuration,
            timeout = 120
        )
        configured = start_forwarder_scheduler(
            address = address,
            port = port,
            scheduler_request = scheduler_request
        )
        return configured
    
    def test_url(
        target_url: str,
        timeout: int
    ) -> bool:
        try:
            response = requests.head(
                url = target_url, 
                timeout = timeout
            )
            if response.status_code == 200:
                return True
            return False
        except requests.ConnectionError:
            return False
        
    def setup_ray(
        logger: any,
        services: any,
        timeout: int
    ):
        logger.info('Setting up ray client')
        start = t.time()
        ray_client = None
        if 0 < len(services):
            ray_dashboard_url = 'http://' + services['ray-dashboard']
            ray_exists = None
            while t.time() - start <= timeout:
                logger.info('Testing ray client url: ' + str(ray_dashboard_url))
                ray_exists = test_url(
                    target_url = ray_dashboard_url,
                    timeout = 5
                )
                logger.info('Ray client exists: ' + str(ray_exists))
                if ray_exists:
                    break
                t.sleep(5)
            if ray_exists:
                ray_client = JobSubmissionClient(
                    address = ray_dashboard_url
                )
                logger.info("Ray setup")
        return ray_client

    def get_ray_job(
        logger: any,
        storage_client: any,
        storage_name: str,
        ray_job_file: str
    ) -> any:
        #logger.info('Ray job path:' + str(ray_job_path))
        ray_job_object = get_object(
            storage_client = storage_client,
            bucket_name = storage_name,
            object_name = 'ray',
            path_replacers = {
                'name': ray_job_file
            },
            path_names = []
        )

        ray_job_object_data = ray_job_object['data']

        current_directory = os.getcwd()
        ray_job_directory = os.path.join(current_directory, 'jobs')

        if not os.path.exists(ray_job_directory):
            logger.info('Make directory')
            os.makedirs(ray_job_directory)
        
        used_ray_job_path = os.path.join(ray_job_directory, ray_job_file)
        
        logger.info('Job writing path:' + str(used_ray_job_path))
        with open(used_ray_job_path, 'w') as file:
            file.write(ray_job_object_data)

        return ray_job_directory

    def submit_ray_job(
        logger: any,
        ray_client: any,
        ray_parameters: any,
        ray_job_file: any,
        working_directory: str,
        ray_job_envs: any
    ) -> any:
        logger.info('Submitting ray job ' + str(ray_job_file) + ' using directory ' + str(working_directory))
        command = "python " + str(ray_job_file)
        if 0 < len(ray_parameters):
            command = command + " '" + json.dumps(ray_parameters) + "'"
        job_id = ray_client.submit_job(
            entrypoint = command,
            runtime_env = {
                'working_dir': str(working_directory),
                'env_vars': ray_job_envs
            }
        )
        return job_id

    def wait_ray_job(
        logger: any,
        ray_client: any,
        ray_job_id: int, 
        waited_status: any,
        timeout: int
    ) -> any:
        logger.info('Waiting ray job ' + str(ray_job_id))
        start = t.time()
        job_status = None
        while t.time() - start <= timeout:
            status = ray_client.get_job_status(ray_job_id)
            logger.info(f"status: {status}")
            if status in waited_status:
                job_status = status
                break
            t.sleep(5)
        job_logs = ray_client.get_job_logs(ray_job_id)
        return job_status, job_logs

    def ray_job_handler(
        logger: any,
        storage_client: any,
        storage_name: str,
        ray_client: any,
        ray_parameters: any,
        ray_job_file: str,
        ray_job_envs: any,
        timeout: int
    ) -> bool:
        logger.info('Setting up ray job')

        ray_job_directory = get_ray_job(
            logger = logger,
            storage_client = storage_client,
            storage_name = storage_name,
            ray_job_file = ray_job_file
        )

        logger.info('Submitting a ray job')
        ray_job_id = submit_ray_job(
            logger = logger,
            ray_client = ray_client,
            ray_parameters = ray_parameters,
            ray_job_file = ray_job_file,
            working_directory = ray_job_directory,
            ray_job_envs = ray_job_envs
        )

        logger.info('Ray batch job id: ' + str(ray_job_id))
        
        ray_job_status, ray_job_logs = wait_ray_job(
            logger = logger,
            ray_client = ray_client,
            ray_job_id = ray_job_id,
            waited_status = {
                JobStatus.SUCCEEDED, 
                JobStatus.STOPPED, 
                JobStatus.FAILED
            }, 
            timeout = timeout
        )
        logger.info('Ray batch job ended:')
        success = True
        if not ray_job_status == JobStatus.SUCCEEDED:
            logger.info('RAY batch job failed')
            success = False
        else:
            logger.info('RAY batch job succeeded')
        logger.info(ray_job_logs)
        return success

    def parse_job_sacct(
        logger: any,
        sacct: any
    ) -> any:
        collected_parameters = {}
        collected_metrics = {}
        logger.info('')
        logger.info('Sacct:')
        for row in sacct.keys():
            logger.info('Row ' + str(row))
            row_metadata = sacct[row]['metadata']
            row_metrics = sacct[row]['metrics']
        
            relevant_metadata = [
                'job-name',
                'state'
            ]
            
            for key, value in row_metadata.items():
                if key in relevant_metadata:
                    logger.info(str(key) + '=' + str(value))
                    collected_parameters[str(row) + '-' + key] = value
        
            relevant_metrics = [
                'ave-cpu-seconds',
                'cpu-time-seconds',
                'elapsed-seconds',
                'total-cpu-seconds',
            ]
            
            for key, value in row_metrics.items():
                if key in relevant_metrics:
                    logger.info(str(key) + '=' + str(value))
                    collected_metrics[str(row) + '-' + key] = value
        
            start_time = row_metrics['start-time']
            submit_time = row_metrics['submit-time']
            end_time = row_metrics['end-time']
        
            submit_date = datetime.fromtimestamp(start_time).strftime('%Y-%m-%d-%H:%M:%S')
            total_start_seconds = (submit_time-start_time)
            total_end_seconds = (end_time-submit_time)
        
            logger.info('submit-date=' + str(submit_date))
            collected_parameters[str(row) + '-submit-date'] = submit_date
            
            logger.info('total-submit-start-seconds=' + str(total_start_seconds))
            collected_metrics[str(row) + '-total-submit-start-seconds'] = total_start_seconds
            
            logger.info('total-start-end-seconds=' + str(total_end_seconds))
            collected_metrics[str(row) + '-total-start-end-seconds'] = total_end_seconds
            
            logger.info('')
        return collected_parameters, collected_metrics

    def parse_job_seff(
        logger: any,
        seff: any
    ) -> any:
        collected_parameters = {}
        collected_metrics = {}
        relevant_metadata = [
            'billed-project',
            'cluster',
            'status'
        ]

        logger.info('')
        logger.info('Seff:')
        seff_metadata = seff['metadata']
        for key,value in seff_metadata.items():
            if key in relevant_metadata:
                logger.info(str(key) + '=' + str(value))
                collected_parameters[key] = value
        
        relevant_metrics = [
            'billing-units',
            'cpu-efficiency-percentage',
            'cpu-efficiency-seconds',
            'cpu-utilized-seconds',
            'job-wall-clock-time-seconds',
            'memory-efficiency-percentage'
        ]


        seff_metrics = seff['metrics']
        for key,value in seff_metrics.items():
            if key in relevant_metrics:
                logger.info(str(key) + '=' + str(value))
                collected_metrics[key] = value

        return collected_parameters, collected_metrics
    
    # BOILERPLATE END
    
    logging.basicConfig(level = logging.INFO)
    logger = logging.getLogger(__name__)

    component_time_start = t.time()

    storage_client, storage_names = setup_storage(
        storage_parameters = storage_parameters
    )

    logger.info('Storage setup')

    output = namedtuple('Output', ['storage_uri', 'run_id'])

    pipeline_bucket = storage_names[-2]

    logger.info('Used bucket:' + str(pipeline_bucket))
    
    logger.info("Variable setup")

    configuration = integration_parameters['configuration']
    scheduler_request = integration_parameters['scheduler-request']
    forwarder_address = integration_parameters['forwarder-address']
    forwarder_port = integration_parameters['forwarder-port']
    forwarding_request = integration_parameters['forwarding-request']
    user = integration_parameters['user']
    job_request = integration_parameters['job-request']
    ray_parameters = integration_parameters['ray-parameters']
    ray_job_file = integration_parameters['ray-job-file']
    ray_job_envs = integration_parameters['ray-job-envs']
    ray_job_timeout = integration_parameters['ray-job-timeout']
    folder_name = integration_parameters['folder-name']
    
    logger.info(forwarder_address)

    logger.info("Starting forwarder")

    forwarder_started = start_forwarder(
        address = forwarder_address, 
        port = forwarder_port,
        configuration = configuration,
        scheduler_request = scheduler_request
    )

    if not forwarder_started:
        return output('none', 'none')

    logger.info("Forwarder started")

    logger.info("Submitting forwarding request")
    logger.info(forwarder_address)

    status_code, forwarding = request_route(
        address = forwarder_address,
        port = forwarder_port,
        route_type = '',
        route_name = 'forwarding-submit',
        path_replacers = {},
        path_names = [],
        route_input = forwarding_request,
        timeout = 240
    )
    
    if not status_code == 200:
        return output('none', 'none')

    logger.info("Request success")

    # failed here

    forwarder_keys = forwarding['keys']
    forwarding_split = forwarder_keys.split(',')
    import_key = forwarding_split[0]

    logger.info("Import key: " + str(import_key))

    if import_key == '0':
        return output('none', 'none')
    
    logger.info("Waiting forwarding services")

    forwarding_timeout = 500
    start = t.time()
    current_services = None
    while t.time() - start <= forwarding_timeout:
        status_code, forwarding_data = request_route(
            address = forwarder_address,
            port = forwarder_port,
            route_type = '',
            route_name = 'forwarding-artifact',
            path_replacers = {
                'type': 'status-imports',
                'user': user,
                'key': import_key
            },
            path_names = [],
            route_input = {},
            timeout = 500
        )

        if not status_code == 200:
            return output('none', 'none')

        if not 'forwarding-status' in forwarding_data:
            return output('none', 'none')
        
        forwarding_status = forwarding_data['forwarding-status']    
        if forwarding_status['cancel'] or forwarding_status['deleted']:
            break

        if forwarding_status['created']:
            current_services = forwarding_status['services']
            break
        t.sleep(5)
    
    if current_services is None:
        return output('none', 'none')
        
    logger.info("Services up")

    logger.info("Submitting job request")

    status_code, job_key = request_route(
        address = forwarder_address,
        port = forwarder_port,
        route_type = '',
        route_name = 'job-submit',
        path_replacers = {},
        path_names = [],
        route_input = job_request,
        timeout = 240
    )

    current_job_key = job_key['key']

    logger.info("Current job key: " + str(current_job_key))

    if not status_code == 200:
        return output('none', 'none')

    if current_job_key == '0':
        return output('none', 'none')

    logger.info("Starting job")
    
    status_code, job_start = request_route(
        address = forwarder_address,
        port = forwarder_port,
        route_type = '',
        route_name = 'job-run',
        path_replacers = {
            'name': user
        },
        path_names = [
            current_job_key
        ],
        route_input = {},
        timeout = 240
    )

    job_start_status = job_start['status']

    logger.info("Job started: " + str(job_start_status))

    if not job_start_status == 'success':
        return output('none', 'none')

    logger.info("Waiting job to run")

    current_jobid = None
    job_timeout = 600
    start = t.time()
    while t.time() - start <= job_timeout:
        status_code, job_data = request_route(
            address = forwarder_address,
            port = forwarder_port,
            route_type = '',
            route_name = 'job-artifact',
            path_replacers = {
                'type': 'status',
                'name': user
            },
            path_names = [
                current_job_key
            ],
            route_input = {},
            timeout = 240
        )

        if not status_code == 200:
            return output('none', 'none')

        if not 'job-status' in job_data:
            return output('none', 'none')

        # failed here
        job_status = job_data['job-status']
        if job_status['cancel'] or job_status['stopped']:
            break

        if job_status['pending'] or job_status['running']:
            current_jobid = job_status['id']
            break

        t.sleep(5)

    if current_jobid is None:
        return output('none', 'none')
    
    logger.info('SLURM job id: ' + str(current_jobid))

    logger.info('Setting up Ray')
    logger.info(current_services)
    ray_client = setup_ray(
        logger = logger,
        services = current_services,
        timeout = 500
    )
    
    if ray_client is None:
        return output('none', 'none')

    logger.info('Ray client setup')

    logger.info('Setting up MLFlow')
   
    setup_mlflow(
        logger = logger,
        mlflow_parameters = mlflow_parameters
    )

    logger.info('MLflow setup')

    with mlflow.start_run() as run:
        run_id = run.info.run_id
        logger.info(f"Run ID: {run_id}")

        logger.info('Running ray job: ' + str(ray_job_file))

        ray_job_success = ray_job_handler(
            logger = logger,
            storage_client = storage_client,
            storage_name = pipeline_bucket,
            ray_client = ray_client,
            ray_parameters = ray_parameters,
            ray_job_file = ray_job_file,
            ray_job_envs = ray_job_envs,
            timeout = ray_job_timeout
        )

        logger.info('Ray job ran: ' + str(ray_job_success))

        status_code, cancel_data = request_route(
            address = forwarder_address,
            port = forwarder_port,
            route_type = '',
            route_name = 'job-cancel',
            path_replacers = {
                'name': user,
            },
            path_names = [
                current_job_key
            ],
            route_input = {},
            timeout = 240
        )
        # Fails here
        logger.info('SLURM job cancel: ' + str(cancel_data))
        if not ray_job_success:
            return output('none', 'none')

        logger.info('Collecting Artifacts')
 
        collected_parameters = {}
        collected_metrics = {}

        logger.info('Hyperarameters')

        for key,value in ray_parameters.items():
            if 'hp-' in key:
                formatted_key = key.replace('hp-', '')
                logger.info(str(key) + '=' + str(value))
                collected_parameters[formatted_key] = value

        logger.info('Getting model parameters')

        parameters_object = get_object(
            storage_client = storage_client,
            bucket_name = pipeline_bucket,
            object_name = 'artifacts',
            path_replacers = {
                'name': folder_name
            },
            path_names = [
                'parameters'
            ]
        )
        parameters_object_data = parameters_object['data']

        logger.info('Logging model')

        trained_model = CNNClassifier()
        trained_model.load_state_dict(parameters_object_data['model'])
        trained_model.eval()
        
        model_name = mlflow_parameters['model-name']
        registered_name = mlflow_parameters['registered-name']
        mlflow.pytorch.log_model(
            trained_model, 
            model_name,
            registered_model_name = registered_name
        )

        logger.info('Getting model predictions')

        predictions_object = get_object(
            storage_client = storage_client,
            bucket_name = pipeline_bucket,
            object_name = 'artifacts',
            path_replacers = {
                'name': folder_name
            },
            path_names = [
                'predictions'
            ]
        ) 
        predictions_object_data = predictions_object['data']

        logger.info("Logging predictions")
        np.save("predictions.npy", predictions_object_data)
        mlflow.log_artifact(
            local_path = "predictions.npy",
            artifact_path = "predicted_qualities/"
        )
        
        logger.info("Logging metrics")
        metrics_object = get_object(
            storage_client = storage_client,
            bucket_name = pipeline_bucket,
            object_name = 'artifacts',
            path_replacers = {
                'name': folder_name
            },
            path_names = [
                'metrics'
            ]
        ) 
        metrics_object_data = metrics_object['data']

        performance = metrics_object_data['performance']
        
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
                collected_metrics[key] = value
                continue
        
        logger.info("Waiting sacct and seff")
        store_timeout = 300
        start = t.time()
        stored = False
        while t.time() - start <= store_timeout:
            status_code, job_data = request_route(
                address = forwarder_address,
                port = forwarder_port,
                route_type = '',
                route_name = 'job-artifact',
                path_replacers = {
                    'type': 'status',
                    'name': user
                },
                path_names = [
                    current_job_key
                ],
                route_input = {},
                timeout = 240
            )

            if not status_code == 200:
                break

            if not 'job-status' in job_data:
                break

            # failed here
            job_status = job_data['job-status']
            if job_status['stored']:
                stored = True
                break

            t.sleep(5)

        if stored:
            logger.info("Fetching sacct")
            status_code, sacct_data = request_route(
                address = forwarder_address,
                port = forwarder_port,
                route_type = '',
                route_name = 'job-artifact',
                path_replacers = {
                    'type': 'sacct',
                    'name': user
                },
                path_names = [
                    current_job_key
                ],
                route_input = {},
                timeout = 300
            )

            if status_code == 200:
                if 'job-sacct' in sacct_data:
                    logger.info("Logging sacct")
                    job_sacct = sacct_data['job-sacct']
                    params, metrics = parse_job_sacct(
                        logger = logger,
                        sacct = job_sacct['job-sacct']
                    )

                    for key,value in params.items():
                        collected_parameters[key] = value

                    for key,value in metrics.items():
                        collected_metrics[key] = value

            logger.info("Fetching seff")
            status_code, seff_data = request_route(
                address = forwarder_address,
                port = forwarder_port,
                route_type = '',
                route_name = 'job-artifact',
                path_replacers = {
                    'type': 'seff',
                    'name': user
                },
                path_names = [
                    current_job_key
                ],
                route_input = {},
                timeout = 240
            )
            
            if status_code == 200:
                if 'job-seff' in seff_data:
                    logger.info("Logging seff")
                    job_seff = seff_data['job-seff']
                    params, metrics = parse_job_seff(
                        logger = logger,
                        sacct = job_seff
                    )

                    for key,value in params.items():
                        collected_parameters[key] = value

                    for key,value in metrics.items():
                        collected_metrics[key] = value

        logger.info("Logging parameters and metrics")

        for key,value in collected_parameters.items():
            mlflow.log_param(key, value)
        logger.info("Parameters logged")

        for key,value in collected_metrics.items():
            mlflow.log_metric(key, value)
        logger.info("Metrics logged")
        
        logger.info("Canceling imports")

        status_code, cancel_data = request_route(
            address = forwarder_address,
            port = forwarder_port,
            route_type = '',
            route_name = 'forwarding-cancel',
            path_replacers = {
                'type': 'imports',
                'user': user,
                'key': import_key
            },
            path_names = [],
            route_input = {},
            timeout = 240
        )

        logger.info("Cancellation success:" + str(cancel_data))
        
        component_time_end = t.time()
        
        logger.info("Storing time")
        gather_time( 
            storage_client = storage_client,
            storage_name = pipeline_bucket,
            time_group = 'component',
            time_name = 'cloud-hpc-train',
            start_time = component_time_start,
            end_time = component_time_end
        )

        #if not model_available:
        #    return output('none', 'none')

        # return str(mlflow.get_artifact_uri())
        return output(mlflow.get_artifact_uri(), run_id)