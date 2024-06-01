import json
import requests
import time as t

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

def stop_proxy(
    proxy_url: str
) -> bool:
    response = requests.post(
        url = proxy_url + '/stop'
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

    seff = json.loads(seff_response.text)['job-seff']
    sacct = json.loads(sacct_response.text)['job-sacct']
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

    current_key = str(len(job_status))
    current_job = job_status[current_key]

    data = [
        current_job['job-running'],
        current_job['job-id'],
        current_job['job-bridges']['services']
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
            break
        t.sleep(10)
    return slurm_job_id, slurm_job_services

def get_previous_job_data(
    proxy_url: str,
    kubeflow_user: str,
    target: str
) -> bool:
    job_status = get_job_status(
        proxy_url = proxy_url,
        kubeflow_user = kubeflow_user,
        target = target
    )

    stored = False
    if 1 < len(job_status):
        previous_key = len(job_status) - 1
        previous_key = str(previous_key)
        previous_job = job_status[previous_key]
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
    target: str
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
                target = target
            )
            logger.info('SLURM job stored: ' + str(job_data[0]))
            if job_data[0]:
                success = True
                break
            t.sleep(10)
    return success

