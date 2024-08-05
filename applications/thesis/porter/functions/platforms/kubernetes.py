from typing import Dict
from flask import current_app

# Check that there isn't deprecation issues
def get_cluster_structure() -> Dict[str, Dict[str,str]]:
    current_app.logger.info('Getting cluster structure')
    regular = current_app.regular_kubernetes_client
    custom = current_app.custom_kubernetes_client
    # Here we get the current cluster name of current context
    # This does not work with in cluster config
    #current_cluster = config.list_kube_config_contexts()[1]['context']['cluster']
    structure = {}
    namespaces = regular.list_namespace().items
    for namespace in namespaces:
        namespace_name = namespace.metadata.name
        
        pods = regular.list_namespaced_pod(namespace_name).items
        pod_names = [pod.metadata.name for pod in pods] 

        services = regular.list_namespaced_service(namespace_name).items
        service_names = [service.metadata.name for service in services]
        
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
        structure[namespace_name] = {'pods': pod_names, 'services': service_names}
    return structure