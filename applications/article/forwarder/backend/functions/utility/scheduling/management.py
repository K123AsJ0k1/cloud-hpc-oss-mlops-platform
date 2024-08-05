
from functions.utility.scheduling.deployment import define_scheduler_deployment, remove_scheduler_deployment
from functions.platforms.kustomize import kustomize_create_deployment, kustomize_delete_deployment
# Created and works
def modify_scheduling(
    scheduler_request: any,
    action: str
):
    deployment_folder = define_scheduler_deployment(
        scheduler_request = scheduler_request
    ) 
    
    deployment_status = 'no deployment'
    
    if action == 'start':
        created = kustomize_create_deployment(
            kustomize_folder = deployment_folder
        )

        if created:
            deployment_status = 'creation success'
        else: 
            deployment_status = 'creation failure'
    if action == 'stop':
        removed = kustomize_delete_deployment(
            kustomize_folder = deployment_folder
        )

        if removed:
            definition_removed = remove_scheduler_deployment()
            if definition_removed:
                deployment_status = 'deletion success'
            else:
                deployment_status = 'deletion failure'
        else:
            deployment_status = 'deletion failure'

    return {'status': deployment_status}