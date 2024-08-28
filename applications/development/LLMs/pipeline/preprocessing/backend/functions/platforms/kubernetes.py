from kubernetes import client, config
from typing import Dict
# created and works
def get_kubernetes_clients():
    try:
        config.load_kube_config()
    except Exception as e:
        print('Kube config error: ' + str(e))
    try:
        config.load_incluster_config()
    except Exception as e:
        print('Incluster config error: ' + str(e))
    regular = client.CoreV1Api()
    custom = client.CustomObjectsApi()
    clients = [
        regular,
        custom
    ]
    return clients
# Refactored and works
def get_cluster_structure(
    kubernetes_clients: any
) -> Dict[str, Dict[str,str]]:
    regular = kubernetes_clients[0]
    custom = kubernetes_clients[1]
    # Here we get the current cluster name of current context
    # This does not work with in cluster config
    #current_cluster = config.list_kube_config_contexts()[1]['context']['cluster']
    cluster = {}
    namespaces = regular.list_namespace().items
    for namespace in namespaces:
        namespace_name = namespace.metadata.name
        
        pods = regular.list_namespaced_pod(namespace_name).items
        pod_names = [pod.metadata.name for pod in pods] 

        services = regular.list_namespaced_service(namespace_name).items
        service_names = [service.metadata.name for service in services]
        '''
        if 'argo-rollouts' in namespace_name:
            objects = custom.list_cluster_custom_object(
                group = 'argoproj.io',
                version = 'v1alpha1',
                plural = 'rollouts'
            )
            rollouts = objects.get('items', [])
            rollout_names = [rollout['metadata']['name'] for rollout in rollouts]
            structure['argo-rollouts'] = {'pods': pod_names, 'services': service_names, 'rollouts': rollout_names}
            continue
        '''
        cluster[namespace_name] = {'pods': pod_names, 'services': service_names}
    structure = {'structure': cluster}
    return structure