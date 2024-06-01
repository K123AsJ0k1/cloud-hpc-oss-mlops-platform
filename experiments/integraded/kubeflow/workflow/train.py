from typing import NamedTuple

@component(
    base_image = "python:3.10",
    packages_to_install = [
        "python-swiftclient",
        "ray[default]",
        "mlflow~=2.12.2", 
        "boto3~=1.21.0",
        "numpy",
        "torch==2.3.0"
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
    allas_parameters: dict,
    ray_parameters: dict,
    metadata_parameters: dict,
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
        #logger.info('Time object path:' + str(time_path))
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

    def gather_slurm_artifacts(
        logger: any,
        proxy_url: str,
        proxy_target: str,
        kubeflow_user: str,
        slurm_job_id: str
    ) -> any:
        collected_parameters = {}
        collected_metrics = {}
        
        logger.info('Collecting SLURM artifacts')
        seff,sacct,logs = get_job_artifacts(
            proxy_url = proxy_url,
            kubeflow_user = kubeflow_user,
            slurm_job_id = slurm_job_id,
            target = proxy_target
        )

        relevant_metadata = [
            'billed-project',
            'cluster',
            'status'
        ]
        
        if not seff is None:
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
        
        if not sacct is None:            
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
            
        artifacts = [
            collected_parameters, 
            collected_metrics,
            logs
        ]

        return artifacts

    def gather_ray_artifacts(
        logger: any,
        allas_client: any,
        allas_bucket: str,
        kubeflow_user: str,
        ray_parameters: any
    ):
        collected_parameters = {}
        collected_metrics = {}
        collected_artifacts = {}    
        job_parameters = ray_parameters['job-parameters']

        logger.info('Training hyperparameters:')
        
        for key,value in job_parameters.items():
            if 'hp-' in key:
                formatted_key = key.replace('hp-', '')
                logger.info(str(key) + '=' + str(value))
                collected_parameters[formatted_key] = value

        logger.info('')
        parameters_path = job_parameters['artifact-path'] + '-parameters'
        logger.info('Used parameters path: ' + str(parameters_path))
        ray_job_artifact_parameters = get_object(
            client = allas_client,
            bucket_name = allas_bucket,
            object_path = parameters_path
        )
        
        if not ray_job_artifact_parameters is None:
            collected_artifacts['parameters'] = ray_job_artifact_parameters

        predictions_path = job_parameters['artifact-path'] + '-predictions'
        logger.info('Used predictions path: ' + str(predictions_path))
        ray_job_artifact_predictions = get_object(
            client = allas_client,
            bucket_name = allas_bucket,
            object_path = predictions_path
        )

        if not ray_job_artifact_predictions is None:
            collected_artifacts['predictions'] = ray_job_artifact_predictions

        metrics_path = job_parameters['artifact-path'] + '-metrics'
        logger.info('Used metrics path: ' + str(metrics_path))
        ray_job_artifact_metrics = get_object(
            client = allas_client,
            bucket_name = allas_bucket,
            object_path = metrics_path
        )

        if not ray_job_artifact_metrics is None:
            performance = ray_job_artifact_metrics['performance']
            logger.info('')
            logger.info('Training metrics:')
            for key,value in performance.items():
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
                    logger.info('')
                    i = 0
                    for class_value in value:
                        formatted_key = key.replace('class', image_labels[i])
                        rounded_value = round(class_value,5)
                        logger.info(str(formatted_key) + '=' + str(rounded_value))
                        collected_metrics[formatted_key] = rounded_value
                        i += 1
                    continue
                rounded_value = round(value,5)
                logger.info(str(key) + '=' + str(rounded_value))
                collected_metrics[key] = rounded_value

        logger.info('')
        time_path = job_parameters['time-folder-path'] + '/ray-job'
        logger.info('Used time path: ' + str(time_path))
        ray_job_times = get_object(
            client = allas_client,
            bucket_name = allas_bucket,
            object_path = time_path
        )
        if not ray_job_times is None:
            logger.info('')
            logger.info('Training times:')
            user_ray_job_times = ray_job_times[kubeflow_user]
            for i in range(0,2):
                object_key = len(user_ray_job_times) - i
                time_object = user_ray_job_times[str(object_key)]
                formatted_key = time_object['name'] + '-total-seconds'
                value = time_object['total-seconds']
                collected_metrics[formatted_key] = value
                logger.info(str(formatted_key) + '=' + str(value))
        
        artifacts = [
            collected_parameters, 
            collected_metrics,
            collected_artifacts
        ]

        return artifacts


    
    '''PROXY'''


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

    def setup_proxy(
        proxy_parameters: str,
        proxy_url: str
    ) -> bool:
        setup_payload = json.dumps(proxy_parameters)
        response = requests.post(
            url = proxy_url + '/setup',
            json = setup_payload
        )
        if response.status_code == 200:
            return True
        return False

    def start_proxy(
        proxy_url: str
    ) -> bool:
        response = requests.post(
            url = proxy_url + '/start'
        )
        if response.status_code == 200:
            return True
        return False

    def submit_batch_job(
        proxy_url: str,
        job_submit: any
    ) -> bool:
        submit_payload = json.dumps(job_submit)
        response = requests.post(
            url = proxy_url + '/submit',
            json = submit_payload 
        )
        submit_status = json.loads(response.text)
        if submit_status['submitted']:
            return True
        return False

    def get_job_status(
        proxy_url: str,
        kubeflow_user: str,
        target: str
    ) -> any:
        response = None
        if target == 'porter':
            metadata = {
                'kubeflow-user': kubeflow_user
            }
            metadata_payload = json.dumps(metadata)
            response = requests.get(
                url = proxy_url + '/job/status',
                json = metadata_payload
            )
        if target == 'submitter':
            response = requests.get(
                url = proxy_url + '/job/status'
            )
        job_status = json.loads(response.text)['job-status']
        return job_status 
    
    def get_bridge_status(
        porter_url: str,
        kubeflow_user: str
    ):
        metadata = {
            'kubeflow-user': kubeflow_user
        }
        metadata_payload = json.dumps(metadata)
        response = requests.get(
            url = porter_url + '/job/bridges',
            json = metadata_payload
        )
        bridge_status = json.loads(response.text)['bridge-status']
        return bridge_status

    def cancel_batch_job(
        proxy_url: str,
        kubeflow_user: str,
        target: str
    ) -> any:
        response = None
        if target == 'porter':
            metadata = {
                'kubeflow-user': kubeflow_user
            }
            metadata_payload = json.dumps(metadata)
            response = requests.post(
                url = proxy_url + '/cancel',
                json = metadata_payload
            )
        if target == 'submitter':
            response = requests.post(
                url = proxy_url + '/cancel'
            )
        job_cancelled = json.loads(response.text)['cancelled']
        return job_cancelled

    def get_job_artifacts(
        proxy_url: str,
        kubeflow_user: str,
        slurm_job_id: str,
        target: str
    ) -> any:
        seff_response = None
        sacct_response = None
        logs_response = None

        if target == 'porter':
            metadata = {
                'kubeflow-user': kubeflow_user,
                'job-id': slurm_job_id
            }
            metadata_payload = json.dumps(metadata)

            seff_response = requests.get(
                url = proxy_url + '/job/seff',
                json = metadata_payload
            )

            sacct_response = requests.get(
                url = proxy_url + '/job/sacct',
                json = metadata_payload
            )

            logs_response = requests.get(
                url = proxy_url + '/job/logs',
                json = metadata_payload
            )

        if target == 'submitter':
            metadata = {
                'job-id': slurm_job_id
            }
            metadata_payload = json.dumps(metadata)

            seff_response = requests.get(
                url = proxy_url + '/job/seff',
                json = metadata_payload
            )

            sacct_response = requests.get(
                url = proxy_url + '/job/sacct',
                json = metadata_payload
            )

            logs_response = requests.get(
                url = proxy_url + '/job/logs',
                json = metadata_payload
            )

        seff = None
        sacct = None
        logs = None
        if seff_response.status_code == 200:
            seff = json.loads(seff_response.text)['job-seff']
        if sacct_response.status_code == 200:
            sacct = json.loads(sacct_response.text)['job-sacct']
        if logs_response.status_code == 200:
            logs = json.loads(logs_response.text)['job-logs']

        return seff,sacct,logs

    def start_slurm_job(
        logger: any,
        proxy_parameters: any,
        proxy_url: str,
        job_submit: any
    ):
        logger.info('Proxy url: ' + str(proxy_url))
        porter_exists = test_url(
            target_url = proxy_url + '/demo',
            timeout = 5
        )
        logger.info('Proxy exists:' + str(porter_exists))
        success = False
        if porter_exists:
            porter_setup = setup_proxy(
                proxy_parameters = proxy_parameters,
                proxy_url = proxy_url
            )
            logger.info('Proxy setup:' + str(porter_setup))
            if porter_setup:
                porter_started = start_proxy(
                    proxy_url = proxy_url
                )
                logger.info('Proxy started:' + str(porter_started))
                if porter_started:
                    job_submitted = submit_batch_job(
                        proxy_url = proxy_url,
                        job_submit = job_submit
                    )
                    logger.info('Job submitted:' + str(job_submitted))
                    if job_submitted:
                        success = True
        return success

    def get_current_job_data(
        proxy_url: str,
        kubeflow_user: str,
        target: str
    ) -> bool:
        job_status = get_job_status(
            proxy_url = proxy_url,
            kubeflow_user = kubeflow_user,
            target = target
        )
        bridge_status = get_bridge_status(
            porter_url = proxy_url,
            kubeflow_user = kubeflow_user
        )
        
        job_running = False
        job_id = ''
        job_services = []
        job_key = ''

        if not job_status is None:
            current_key = str(len(job_status))
            current_job = job_status[current_key]
            job_running = current_job['job-running']
            job_id = current_job['job-id']
        if not bridge_status is None:
            job_services = bridge_status['services']
            job_key = bridge_status['submitter-key']

        data = [
            job_running,
            job_id,
            job_services,
            job_key
        ]

        return  data

    def wait_slurm_job(
        logger: any,
        proxy_url: str,
        kubeflow_user: str,
        timeout: int,
        wait_services: bool,
        target: str
    ):
        logger.info('Waiting SLURM job running')
        slurm_job_id = None
        slurm_job_services = None
        slurm_job_key = None
        start = t.time()
        while t.time() - start <= timeout:
            job_data = get_current_job_data(
                proxy_url = proxy_url,
                kubeflow_user = kubeflow_user,
                target = target
            )

            logger.info('SLURM job running: ' + str(job_data[0]))
            if job_data[0]:
                if wait_services and len(job_data[2]) == 0: 
                    t.sleep(10)
                    continue
                slurm_job_id = job_data[1]
                slurm_job_services = job_data[2]
                slurm_job_key = job_data[3]
                break
            t.sleep(10)
        return slurm_job_id, slurm_job_services, slurm_job_key

    def get_previous_job_data(
        proxy_url: str,
        kubeflow_user: str,
        target: str,
        job_key: str
    ) -> bool:
        job_status = get_job_status(
            proxy_url = proxy_url,
            kubeflow_user = kubeflow_user,
            target = target
        )

        stored = False
        if not job_status is None:
            if job_key in job_status:
                previous_job = job_status[job_key]
                stored = previous_job['job-stored']

        data = [
            stored
        ]

        return data

    def gather_slurm_job(
        logger: any,
        proxy_url: str,
        kubeflow_user: str,
        timeout: int,
        target: str,
        slurm_job_key: str
    ) -> bool:
        job_cancelled = cancel_batch_job(
            proxy_url = proxy_url,
            kubeflow_user = kubeflow_user,
            target = target
        )
        success = False
        logger.info('SLURM batch job cancelled: ' + str(job_cancelled))
        
        if job_cancelled:
            start = t.time()
            logger.info('Waiting SLURM job storing')
            while t.time() - start <= timeout:
                job_data = get_previous_job_data(
                    proxy_url = proxy_url,
                    kubeflow_user = kubeflow_user,
                    target = target,
                    job_key = slurm_job_key
                )
                logger.info('SLURM job stored: ' + str(job_data[0]))
                if job_data[0]:
                    success = True
                    t.sleep(30)
                    break
                t.sleep(10)
        return success


    '''RAY'''

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
        allas_client: any,
        allas_bucket: str,
        ray_job_path: str
    ) -> any:
        logger.info('Ray job path:' + str(ray_job_path))
        ray_job = get_object(
            client = allas_client,
            bucket_name = allas_bucket,
            object_path = ray_job_path
        )

        ray_job_name = ray_job_path.split('/')[-1]

        current_directory = os.getcwd()
        ray_job_directory = os.path.join(current_directory, 'jobs')

        if not os.path.exists(ray_job_directory):
            logger.info('Make directory')
            os.makedirs(ray_job_directory)
        
        ray_job_file = ray_job_name + '.py'
        used_ray_job_path = os.path.join(ray_job_directory, ray_job_file)
        
        logger.info('Job writing path:' + str(used_ray_job_path))
        with open(used_ray_job_path, 'w') as file:
            file.write(ray_job)

        return ray_job_file, ray_job_directory

    def submit_ray_job(
        logger: any,
        ray_client: any,
        ray_parameters: any,
        job_file: any,
        working_directory: str,
        job_envs: any
    ) -> any:
        logger.info('Submitting ray job ' + str(job_file) + ' using directory ' + str(working_directory))
        command = "python " + str(job_file)
        if 0 < len(ray_parameters):
            command = command + " '" + json.dumps(ray_parameters) + "'"
        job_id = ray_client.submit_job(
            entrypoint = command,
            runtime_env = {
                'working_dir': str(working_directory),
                'env_vars': job_envs
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
        allas_client: any,
        allas_bucket: any,
        ray_client: any,
        ray_parameters: any,
        ray_job_path: str,
        ray_job_envs: any,
        timeout: int
    ) -> bool:
        logger.info('Setting up ray job')

        ray_job_file, ray_job_directory = get_ray_job(
            logger = logger,
            allas_client = allas_client,
            allas_bucket = allas_bucket,
            ray_job_path = ray_job_path
        )

        logger.info('Submitting a ray job')
        ray_job_id = submit_ray_job(
            logger = logger,
            ray_client = ray_client,
            ray_parameters = ray_parameters,
            job_file = ray_job_file,
            working_directory = ray_job_directory,
            job_envs = ray_job_envs
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


    '''PYTORCH'''


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


    
    '''MLFLOW'''


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

    
    ''' END OF FUNCTIONS '''
    
    time_start = t.time()

    logging.basicConfig(level = logging.INFO)
    logger = logging.getLogger(__name__)

    output = namedtuple('Output', ['storage_uri', 'run_id'])

    allas_client = setup_allas(
        parameters = allas_parameters
    )
    allas_bucket = allas_parameters['allas-bucket']
    logger.info('Allas client setup')

    proxy_target = metadata_parameters['proxy-target']
    proxy_url = metadata_parameters['proxy-url']
    proxy_parameters = metadata_parameters['proxy-parameters']
    kubeflow_user = metadata_parameters['kubeflow-user']
    job_submit = metadata_parameters['job-submit']
    slurm_wait_timeout = metadata_parameters['slurm-wait-timeout']
    slurm_service_wait = metadata_parameters['slurm-service-wait']
    ray_client_timeout = metadata_parameters['ray-client-timeout']
    ray_job_path = metadata_parameters['ray-job-path']
    ray_job_envs = metadata_parameters['ray-job-envs']
    ray_job_timeout = metadata_parameters['ray-job-timeout']
    slurm_gather_timeout = metadata_parameters['slurm-gather-timeout']
    time_folder_path = metadata_parameters['time-folder-path']
    
    started = start_slurm_job(
        logger = logger,
        proxy_parameters = proxy_parameters,
        proxy_url = proxy_url,
        job_submit = job_submit
    )

    if not started:
        return output('none', 'none')
    

    slurm_job_id, slurm_job_services, slurm_job_key = wait_slurm_job(
        logger = logger,
        proxy_url = proxy_url,
        kubeflow_user = kubeflow_user,
        timeout = slurm_wait_timeout,
        wait_services = slurm_service_wait,
        target = proxy_target
    )

    logger.info('SLURM job id: ' + str(slurm_job_id))
    
    if slurm_job_id is None:
        return output('none', 'none')
    
    ray_client = setup_ray(
        logger = logger,
        services = slurm_job_services,
        timeout = ray_client_timeout
    )
    logger.info('Ray client setup')
    
    if ray_client is None:
        return output('none', 'none')

    logger.info('Ray client setup')
   
    setup_mlflow(
        logger = logger,
        mlflow_parameters = mlflow_parameters
    )

    logger.info('MLflow setup')

    with mlflow.start_run() as run:
        run_id = run.info.run_id
        logger.info(f"Run ID: {run_id}")

        logger.info('Running ray job')

        ray_job_success = ray_job_handler(
            logger = logger,
            allas_client = allas_client,
            allas_bucket = allas_bucket,
            ray_client = ray_client,
            ray_parameters = ray_parameters,
            ray_job_path = ray_job_path,
            ray_job_envs = ray_job_envs,
            timeout = ray_job_timeout
        )

        logger.info('Ray job ran: ' + str(ray_job_success))

        if not ray_job_success:
            return output('none', 'none')

        logger.info('Collecting Artifacts')

        collected_parameters = {}
        collected_metrics = {}

        ray_artifacts = gather_ray_artifacts(
            logger = logger,
            allas_client = allas_client,
            allas_bucket = allas_bucket,
            kubeflow_user = kubeflow_user,
            ray_parameters = ray_parameters
        )
        
        if 0 < len(ray_artifacts[0]):
            for key,value in ray_artifacts[0].items():
                collected_parameters[key] = value
        if 0 < len(ray_artifacts[1]):
            for key,value in ray_artifacts[1].items():
                collected_metrics[key] = value

        model_available = False
        if 0 < len(ray_artifacts[2]):
            if 'parameters' in ray_artifacts[2]:
                logger.info("Logging model")
                trained_model = CNNClassifier()
                trained_model.load_state_dict(ray_artifacts[2]['parameters']['model'])
                trained_model.eval()
                
                model_name = mlflow_parameters['model-name']
                registered_name = mlflow_parameters['registered-name']
                mlflow.pytorch.log_model(
                    trained_model,
                    model_name,
                    registered_model_name = registered_name
                )

                #logging.info(f"Saving model to: {saved_model.path}")
                #torch.save(trained_model,saved_model.path)
                #with open(saved_model.path, 'wb') as fp:
                #    pickle.dump(trained_model, fp, pickle.HIGHEST_PROTOCOL)
                model_available = True

            if 'predictions' in ray_artifacts[2]:
                logger.info("Logging predictions")
                np.save("predictions.npy", ray_artifacts[2]['predictions'])
                mlflow.log_artifact(
                    local_path = "predictions.npy",
                    artifact_path = "predicted_qualities/"
                )

        gathered = gather_slurm_job(
            logger = logger,
            proxy_url = proxy_url,
            kubeflow_user = kubeflow_user,
            timeout = slurm_gather_timeout,
            target = proxy_target,
            slurm_job_key = slurm_job_key
        )

        if gathered:
            slurm_artifacts = gather_slurm_artifacts(
                logger = logger,
                proxy_target = proxy_target,
                proxy_url = proxy_url,
                kubeflow_user = kubeflow_user,
                slurm_job_id = slurm_job_id
            )

            if 0 < len(slurm_artifacts[0]):
                for key,value in slurm_artifacts[0].items():
                    collected_parameters[key] = value

            if 0 < len(slurm_artifacts[1]):
                for key,value in slurm_artifacts[1].items():
                    collected_metrics[key] = value

        logger.info("Logging parameters and metrics")

        for key,value in collected_parameters.items():
            mlflow.log_param(key, value)
        logger.info("Parameters logged")

        for key,value in collected_metrics.items():
            mlflow.log_metric(key, value)
        logger.info("Metrics logged")
        
        time_end = t.time()
        
        gather_time(
            logger = logger,
            allas_client = allas_client,
            allas_bucket =  allas_bucket,
            kubeflow_user = kubeflow_user,
            time_folder_path = time_folder_path,
            object_name = 'components',
            action_name = 'integration-train',
            start_time = time_start,
            end_time = time_end
        ) 

        if not model_available:
            return output('none', 'none')

        # return str(mlflow.get_artifact_uri())
        return output(mlflow.get_artifact_uri(), run_id)