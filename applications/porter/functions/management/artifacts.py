
from functions.management.objects import get_objects
from functions.metrics.seff import parse_seff_dict
from functions.metrics.sacct import parse_sacct_dict
# Created and works
def fetch_job_status(
    file_lock: any,
    allas_client: any,
    allas_bucket: str,
    kubeflow_user:str
) -> any:
    submitters_status = get_objects(
        file_lock = file_lock,
        allas_client = allas_client,
        allas_bucket = allas_bucket,
        object = 'submitters-status',
        replacers = {}
    )
    user_jobs = None
    if not submitters_status is None:
        if kubeflow_user in submitters_status:
            user_jobs = submitters_status[kubeflow_user]
    return {'job-status': user_jobs}
# Created
def fetch_bridge_status(
    file_lock: any,
    allas_client: any,
    allas_bucket: str,
    kubeflow_user: str    
) -> any:
    porter_status = get_objects(
        file_lock = file_lock,
        allas_client = allas_client,
        allas_bucket = allas_bucket,
        object = 'porter-status',
        replacers = {}
    )
    user_bridges = None 
    if not porter_status is None:
        if kubeflow_user in porter_status:
            user_bridges = porter_status[kubeflow_user]
    return {'bridge-status': user_bridges}
# Created and works
def fetch_job_seff(
    file_lock: any,
    allas_client: any,
    allas_bucket: str,
    kubeflow_user:str,
    job_id: str
) -> any:
    user_seff = get_objects(
        file_lock = file_lock,
        allas_client = allas_client,
        allas_bucket = allas_bucket,
        object = 'submitters-object',
        replacers = {
            'purpose': 'MONITOR', 
            'folder': kubeflow_user,
            'object': 'seff'
        }
    )
    wanted_seff = {'job-seff':{}}
    if not user_seff is None:
        for values in user_seff.values():
            if values['Job ID'] == job_id:
                formatted_metrics, formatted_metadata = parse_seff_dict(
                    seff_data = values
                )
                wanted_seff['job-seff']['metrics'] = formatted_metrics
                wanted_seff['job-seff']['metadata'] = formatted_metadata
    return wanted_seff
# Created and works
def fetch_job_sacct(
    file_lock: any,
    allas_client: any,
    allas_bucket: str,
    kubeflow_user:str,
    job_id: str
) -> any:
    user_sacct = get_objects(
        file_lock = file_lock,
        allas_client = allas_client,
        allas_bucket = allas_bucket,
        object = 'submitters-object',
        replacers = {
            'purpose': 'MONITOR', 
            'folder': kubeflow_user,
            'object': 'sacct'
        }
    )
    wanted_sacct = {'job-sacct':{}}
    if not user_sacct is None:
        for rows in user_sacct.values():
            first_row = rows['1']
            if first_row['JobID'] == job_id:
                key = 1
                for sample in rows.values():
                    formatted_metrics, formatted_metadata = parse_sacct_dict(
                        sacct_data = sample
                    )
                    wanted_sacct['job-sacct'][str(key)] = {
                        'metrics': formatted_metrics,
                        'metadata': formatted_metadata
                    }
                    key += 1
    return wanted_sacct
# Created and works
def fetch_job_logs(
    file_lock: any,
    allas_client: any,
    allas_bucket: str,
    kubeflow_user:str,
    job_id: str
) -> any:
    user_logs = get_objects(
        file_lock = file_lock,
        allas_client = allas_client,
        allas_bucket = allas_bucket,
        object = 'submitters-object',
        replacers = {
            'purpose': 'LOGS', 
            'folder': kubeflow_user,
            'object': job_id
        }
    )
    wanted_logs = {'job-logs': []}
    if not user_logs is None:
        wanted_logs['job-logs'] = user_logs
    return wanted_logs
