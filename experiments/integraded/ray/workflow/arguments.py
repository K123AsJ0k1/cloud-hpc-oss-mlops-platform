KUBEFLOW_USERNAME = 'user@example.com'

allas_bucket = '()'
allas_parameters = {
    "pre_auth_url": str(_pre_auth_url),
    "pre_auth_token": str(given_token),
    "user_domain_name": str(_user_domain_name),
    "project_domain_name": str(_project_domain_name),
    "project_name": str(_project_name),
    'auth_version': str(_auth_version),
    'allas-bucket': allas_bucket
}

job_submit = {
    'submit': {
        'job-name': 'ray-cluster',
        'job-enviroment': {
            'venv': {
                'name': 'exp_venv',
                'packages': []
            }
        },
        'job-bridges':{
            'key-name': 'bridge_key',
            'connections': []
        }
    }
}

proxy_parameters = {
    'allas-parameters': allas_parameters,
    'kubeflow-user': KUBEFLOW_USERNAME,
    'remote-target': 'mahti'
}

metadata_parameters = {
    'proxy-target': 'submitter',
    'proxy-url': 'http://127.0.0.1:5556',
    'proxy-parameters': proxy_parameters,
    'kubeflow-user': KUBEFLOW_USERNAME,
    'job-submit': job_submit,
    'slurm-wait-timeout': 500,
    'slurm-service-wait': False,
    'ray-services': {
        'ray-dashboard': '127.0.0.1:8280'
    },
    'ray-client-timeout': 500,
    'ray-job-path': 'BRIDGE/JOBS/user@example.com/RAY/ray-train',
    'ray-job-envs': {},
    'ray-job-timeout': 1000,
    'slurm-gather-timeout': 500,
    'time-folder-path': 'BRIDGE/TIMES'
}

ray_parameters = {
    'allas-parameters': allas_parameters,
    'job-parameters': {
        'data-folder-path': 'BRIDGE/DATA/user@example.com',
        'kubeflow-user': KUBEFLOW_USERNAME,
        'artifact-path': 'EXPERIMENT/ARTIFACTS/ray',
        'time-folder-path': 'BRIDGE/TIMES',
        'train-print-rate': 2000,
        'hp-train-batch-size': 4,
        'hp-test-batch-size': 4,
        'hp-seed': 42,
        'hp-epochs': 5,
        'hp-learning-rate': 0.001,
        'hp-momentum': 0.9
    }
}