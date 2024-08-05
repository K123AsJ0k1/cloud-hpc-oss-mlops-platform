import yaml
import os
import re 
import subprocess
import time
import shutil

from functions.management.objects import get_objects, set_objects, get_folder_objects, delete_folder_objects
from functions.management.storage import store_action_time
# Refactored
def get_users_with_deployable_bridges(
    file_lock: any,
    allas_client: any,
    allas_bucket: str  
) -> any:
    time_start = time.time()
    
    submitters_status = get_objects(
        file_lock = file_lock,
        allas_client = allas_client,
        allas_bucket = allas_bucket,
        object = 'submitters-status',
        replacers = {}
    )
    
    porter_status = get_objects(
        file_lock = file_lock,
        allas_client = allas_client,
        allas_bucket = allas_bucket,
        object = 'porter-status',
        replacers = {}
    )
    bridges = {}
    if not submitters_status is None and not porter_status is None:
        for kubeflow_user in porter_status.keys():
            user_bridges = porter_status[kubeflow_user]

            bridges_created = user_bridges['created']
            job_connections = user_bridges['connections']
            submitter_key = user_bridges['submitter-key']

            current_job = submitters_status[kubeflow_user][submitter_key]
            
            job_start = current_job['job-start']
            job_ready = current_job['job-ready']
            job_running = current_job['job-running']

            if (job_start or job_ready or job_running) and not bridges_created:
                if 0 < len(job_connections):
                    bridges[kubeflow_user] = job_connections

    store_action_time(
        file_lock = file_lock,
        allas_client = allas_client,
        allas_bucket = allas_bucket,
        metadata = {
            'type': 'TIMES',
            'area': 'bridges'
        },
        time_start = time_start,
        action_name = 'get-users-with-deployable-bridges'
    )

    return bridges
# Created and works
def set_formatted_user(
    kubeflow_user: str   
) -> any:
    return re.sub(r'[^a-z0-9]+', '-', kubeflow_user)
# Craeted and works
def set_kustomize_folder(
    kubeflow_user: str
):
    formatted_user = set_formatted_user(
        kubeflow_user = kubeflow_user
    )
    kustomize_folder = 'functions/bridges/' + formatted_user
    return kustomize_folder
# Refactored
def define_user_bridges(
    file_lock: any,
    allas_client: any,
    allas_bucket: str,
    kubeflow_user: str,
    bridges: any
) -> any:  
    time_start = time.time()

    formatted_user = set_formatted_user(
        kubeflow_user = kubeflow_user
    )
    
    kustomize_folder = set_kustomize_folder(
        kubeflow_user = kubeflow_user
    )

    bridge_kustomization_yaml_path = kustomize_folder + '/kustomization.yaml'
    os.makedirs(kustomize_folder, exist_ok=True)
    
    namespace = None
    with open('functions/templates/namespace.yaml','r') as f:
        namespace = yaml.safe_load(f)
    endpoints = None
    with open('functions/templates/endpoints.yaml','r') as f:
        endpoints = yaml.safe_load(f)
    service = None
    with open('functions/templates/service.yaml','r') as f:
        service = yaml.safe_load(f)
    kustomization = None
    with open('functions/templates/kustomization.yaml','r') as f:
        kustomization = yaml.safe_load(f)
    
    namespace_yaml_path =  kustomize_folder + '/namespace.yaml' 
    namespace_name = namespace['metadata']['name'] + '-' + formatted_user
    namespace['metadata']['name'] = namespace_name
    with open(namespace_yaml_path, 'w') as f:
        yaml.dump(namespace, f, sort_keys = False)

    services = {}
    file_names = ['namespace.yaml']
    for bridge in bridges:
        name = bridge['name']
        cloud_private_ip = bridge['cloud-private-ip']
        cloud_port = bridge['cloud-port']
        # Service-endpoints need to have the same name
        service_endpoints_name = name 
        
        endpoints['metadata']['name'] = service_endpoints_name 
        endpoints['subsets'][0]['addresses'][0]['ip'] = cloud_private_ip
        endpoints['subsets'][0]['ports'][0]['port'] = int(cloud_port)
        
        endpoints_yaml_path = kustomize_folder + '/' + name + '-endpoints.yaml'
        with open(endpoints_yaml_path, 'w') as f:
            yaml.dump(endpoints, f, sort_keys = False)
        file_names.append(name + '-endpoints.yaml')

        service['metadata']['name'] = service_endpoints_name
        service['spec']['ports'][0]['port'] = int(cloud_port)
        service['spec']['ports'][0]['targetPort'] = int(cloud_port)
        # Example http://remote-ray-bridge.default.svc.cluster.local:8280
        services[name] = service_endpoints_name + '.' + namespace_name + '.svc.cluster.local:' + str(cloud_port)
        service_yaml_path = kustomize_folder + '/' + name + '-service.yaml'
        with open(service_yaml_path, 'w') as f:
            yaml.dump(service, f, sort_keys = False)
        file_names.append(name + '-service.yaml')

    kustomization['namespace'] = namespace_name
    kustomization['resources'] = file_names
    with open(bridge_kustomization_yaml_path, 'w') as f:
        yaml.dump(kustomization, f, sort_keys = False)

    store_action_time(
        file_lock = file_lock,
        allas_client = allas_client,
        allas_bucket = allas_bucket,
        metadata = {
            'type': 'TIMES',
            'area': 'bridges'
        },
        time_start = time_start,
        action_name = 'define-user-bridges'
    )

    return services
# Refactored
def get_users_with_removable_bridges(
    file_lock: any,
    allas_client: any,
    allas_bucket: str
) -> any:
    time_start = time.time()

    submitters_status = get_objects(
        file_lock = file_lock,
        allas_client = allas_client,
        allas_bucket = allas_bucket,
        object = 'submitters-status',
        replacers = {}
    )

    porter_status = get_objects(
        file_lock = file_lock,
        allas_client = allas_client,
        allas_bucket = allas_bucket,
        object = 'porter-status',
        replacers = {}
    )
    users = []
    if not submitters_status is None and not porter_status is None:
        for kubeflow_user in porter_status.keys():
            if 1 < len(submitters_status[kubeflow_user]):
                # There might be cases, where job completion is faster than scaling
                # This would cause this to fail
                user_bridges = porter_status[kubeflow_user]
                submitter_key = user_bridges['submitter-key']
                job_connections = user_bridges['connections']

                bridges_created = user_bridges['created']
                bridges_deleted = user_bridges['deleted']
                
                previous_job = submitters_status[kubeflow_user][submitter_key]

                job_failed = previous_job['job-failed']
                job_complete = previous_job['job-complete']
                
                if (job_failed or job_complete) and bridges_created and not bridges_deleted:
                    if 0 < len(job_connections):
                        users.append(kubeflow_user)
    
    store_action_time(
        file_lock = file_lock,
        allas_client = allas_client,
        allas_bucket = allas_bucket,
        metadata = {
            'type': 'TIMES',
            'area': 'bridges'
        },
        time_start = time_start,
        action_name = 'get-users-with-removable-bridges'
    )
    
    return users
# Created and works
def store_bridge_yamls(
    file_lock: any,
    logger: any,
    allas_client: any,
    allas_bucket: str,
    kubeflow_user: str
):
    time_start = time.time()

    user_kustomize_folder = set_kustomize_folder(
        kubeflow_user = kubeflow_user
    )
    files = os.listdir(user_kustomize_folder)
    for file in files:
        file_name = file.split('.')[0]
        file_path = user_kustomize_folder + '/' + file
        yaml_data = None
        
        with open(file_path,'r') as f:
            yaml_data = yaml.safe_load(f)

        set_objects(
            file_lock = file_lock,
            allas_client = allas_client,
            allas_bucket = allas_bucket,
            object = 'monitor-file',
            replacers = {
                'purpose': 'KUSTOMIZE',
                'folder': kubeflow_user,
                'name': file_name
            },
            overwrite = True,
            object_data = yaml_data
        )

    store_action_time(
        file_lock = file_lock,
        allas_client = allas_client,
        allas_bucket = allas_bucket,
        metadata = {
            'type': 'TIMES',
            'area': 'bridges'
        },
        time_start = time_start,
        action_name = 'store-bridge-yamls'
    )
# Created and works
def get_bridge_yamls(
    file_lock: any,
    logger: any,
    allas_client: any,
    allas_bucket: str,
    kubeflow_user: str,
):
    time_start = time.time()

    files = get_folder_objects(
        file_lock = file_lock,
        allas_client = allas_client,
        allas_bucket = allas_bucket,
        object = 'monitor-object',
        replacers = {
            'purpose': 'KUSTOMIZE',
            'object': kubeflow_user
        }
    )
    
    # There might be a need to delete objects in allas and files after success
    user_kustomize_folder = set_kustomize_folder(
        kubeflow_user = kubeflow_user
    )

    os.makedirs(user_kustomize_folder, exist_ok=True)
    for file_name, file_data in files.items():
        file_path = user_kustomize_folder + '/' + file_name + '.yaml'
        with open(file_path, 'w') as f:
            yaml.dump(file_data, f, sort_keys = False)
    
    store_action_time(
        file_lock = file_lock,
        allas_client = allas_client,
        allas_bucket = allas_bucket,
        metadata = {
            'type': 'TIMES',
            'area': 'bridges'
        },
        time_start = time_start,
        action_name = 'get-bridge-yamls'
    )
# Created and works
def delete_bridge_yamls(
    file_lock: any,
    logger: any,
    allas_client: any,
    allas_bucket: str,
    kubeflow_user: str,
):
    time_start = time.time()

    delete_folder_objects(
        file_lock = file_lock,
        allas_client = allas_client,
        allas_bucket = allas_bucket,
        object = 'monitor-object',
        replacers = {
            'purpose': 'KUSTOMIZE',
            'object': kubeflow_user
        }
    )

    store_action_time(
        file_lock = file_lock,
        allas_client = allas_client,
        allas_bucket = allas_bucket,
        metadata = {
            'type': 'TIMES',
            'area': 'bridges'
        },
        time_start = time_start,
        action_name = 'delete-bridge-yamls'
    )
# Refactored and works
def create_or_delete_bridges(
    file_lock: any,
    logger: any,
    allas_client: any,
    allas_bucket: str,
    kubeflow_user: str,
    action: str
) -> bool:
    time_start = time.time()

    user_kustomize_folder = set_kustomize_folder(
        kubeflow_user = kubeflow_user
    )
    
    # It seems that this gets not found errors, when a host computer
    # has restarted and made the cluster run
    # Fortunelly this is mostly mitigated by the scaler 

    success = False
    if action == 'create':
        if not os.path.exists(user_kustomize_folder):
            return False
        
        argument = ['kubectl', 'apply', '-k', user_kustomize_folder]
        try:
            result = subprocess.run(
                args = argument,
                capture_output = True,
                text = True,
                check = True 
            )
            output = result.stdout
            logger.info('Bridge creation result:\n' + str(output))
            success = True
        except Exception as e:
            logger.error('Bridge creation error')
            logger.error(e)
            
        
    if action == 'delete':
        argument = ['kubectl', 'delete', '-k', user_kustomize_folder]
        
        try:
            result = subprocess.run(
                args = argument,
                capture_output = True,
                text = True,
                check = True 
            )
            output = result.stdout
            logger.info('Bridge deletion result:\n' + str(output))
            success = True
        except Exception as e:
            logger.error('Bridge deletion error')
            logger.error(e)
            

    store_action_time(
        file_lock = file_lock,
        allas_client = allas_client,
        allas_bucket = allas_bucket,
        metadata = {
            'type': 'TIMES',
            'area': 'bridges'
        },
        time_start = time_start,
        action_name = 'create-or-delete-bridges'
    )
    
    return success
# Created and works
def bridge_scaler(
    file_lock: any,
    logger: any,
    allas_client: any,
    allas_bucket: str  
):
    time_start = time.time() 

    # We will assert deployment determinism 
    # by only enabling single bridge instance for a single job
    removable_bridges = get_users_with_removable_bridges(
        file_lock = file_lock,
        allas_client = allas_client,
        allas_bucket = allas_bucket
    ) 
    
    if not len(removable_bridges) == 0:
        porter_status = get_objects(
            file_lock = file_lock,
            allas_client = allas_client,
            allas_bucket = allas_bucket,
            object = 'porter-status',
            replacers = {}
        )

        if not porter_status is None:
            for kubeflow_user in removable_bridges:
                user_kustomize_folder = set_kustomize_folder(
                    kubeflow_user = kubeflow_user
                )
                
                if not os.path.exists(user_kustomize_folder):
                    get_bridge_yamls(
                        file_lock = file_lock,
                        logger = logger,
                        allas_client = allas_client,
                        allas_bucket = allas_bucket,
                        kubeflow_user = kubeflow_user
                    )

                bridges_deleted = create_or_delete_bridges(
                    file_lock = file_lock,
                    logger = logger,
                    allas_client = allas_client,
                    allas_bucket = allas_bucket,
                    kubeflow_user = kubeflow_user,
                    action = 'delete'
                )

                if bridges_deleted:
                    shutil.rmtree(user_kustomize_folder)
                    delete_bridge_yamls(
                        file_lock = file_lock,
                        logger = logger,
                        allas_client = allas_client,
                        allas_bucket = allas_bucket,
                        kubeflow_user = kubeflow_user
                    )
                    logger.info('Bridges of ' + str(kubeflow_user) + ' have been properly deleted')
                else:
                    logger.info('Bridges of ' + str(kubeflow_user) + ' were not properly deleted')

                user_bridges = porter_status[kubeflow_user]
                user_bridges['deleted'] = True
                porter_status[kubeflow_user] = user_bridges
                
                set_objects(
                    file_lock = file_lock,
                    allas_client = allas_client,
                    allas_bucket = allas_bucket,
                    object = 'porter-status',
                    replacers = {},
                    overwrite = True,
                    object_data = porter_status
                )

    deployable_bridges = get_users_with_deployable_bridges(
        file_lock = file_lock,
        allas_client = allas_client,
        allas_bucket = allas_bucket
    )
   
    if not len(deployable_bridges) == 0:
        porter_status = get_objects(
            file_lock = file_lock,
            allas_client = allas_client,
            allas_bucket = allas_bucket,
            object = 'porter-status',
            replacers = {}
        )

        if not porter_status is None:
            for kubeflow_user, bridges in deployable_bridges.items():
                created_services = define_user_bridges(
                    file_lock = file_lock,
                    allas_client = allas_client,
                    allas_bucket = allas_bucket,
                    kubeflow_user = kubeflow_user,
                    bridges = bridges
                )

                bridges_created = create_or_delete_bridges(
                    file_lock = file_lock,
                    logger = logger,
                    allas_client = allas_client,
                    allas_bucket = allas_bucket,
                    kubeflow_user = kubeflow_user,
                    action = 'create'
                )
                
                if bridges_created:
                    store_bridge_yamls(
                        file_lock = file_lock,
                        logger = logger,
                        allas_client = allas_client,
                        allas_bucket = allas_bucket,
                        kubeflow_user = kubeflow_user
                    )
                    logger.info('Bridges for ' + str(kubeflow_user) + ' have been properly created')
                else:
                    logger.info('Bridges for ' + str(kubeflow_user) + ' were not properly created')
                
                user_bridges = porter_status[kubeflow_user]
                user_bridges['created'] = True
                user_bridges['services'] = created_services
                porter_status[kubeflow_user] = user_bridges
                
                set_objects(
                    file_lock = file_lock,
                    allas_client = allas_client,
                    allas_bucket = allas_bucket,
                    object = 'porter-status',
                    replacers = {},
                    overwrite = True,
                    object_data = porter_status
                )

    store_action_time(
        file_lock = file_lock,
        allas_client = allas_client,
        allas_bucket = allas_bucket,
        metadata = {
            'type': 'TIMES',
            'area': 'bridges'
        },
        time_start = time_start,
        action_name = 'bridge-scaler'
    )