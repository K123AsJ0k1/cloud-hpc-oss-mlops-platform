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

ray_parameters = {
    'allas-parameters': allas_parameters,
    'job-parameters': {
        'data-folder-path': 'BRIDGE/DATA/user@example.com',
        'kubeflow-user': KUBEFLOW_USERNAME,
        'artifact-path': 'EXPERIMENT/ARTIFACTS/kubeflow',
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

proxy_parameters = {
    'allas-parameters': allas_parameters
}

job_submit = {
    'kubeflow-user': KUBEFLOW_USERNAME,
    'submit': {
        'job-name': 'ray-cluster',
        'job-enviroment': {
            'venv': {
                'name': 'exp_venv',
                'packages': []
            }
        },
        'job-key': 'bridge_key',
        'job-connections':[
            {
                'name': 'ray-dashboard',
                'cloud-private-ip': '192.168.1.13',
                'cloud-port': '8280'
            }
        ]
    }
}

metadata_parameters = {
    'proxy-target': 'porter',
    'proxy-url': 'http://porter-service.monitoring.svc.cluster.local:5555',
    'proxy-parameters': proxy_parameters,
    'kubeflow-user': KUBEFLOW_USERNAME,
    'job-submit': job_submit,
    'slurm-wait-timeout': 800,
    'slurm-service-wait': True,
    'ray-client-timeout': 800,
    'ray-job-path': 'BRIDGE/JOBS/user@example.com/RAY/kubeflow-train',
    'ray-job-envs': {},
    'ray-job-timeout': 1000,
    'slurm-gather-timeout': 800,
    'time-folder-path': 'BRIDGE/TIMES'
}

mlflow_parameters = {
    'tracking-uri': 'http://mlflow.mlflow.svc.cluster.local:5000',
    's3-endpoint-url': 'http://mlflow-minio-service.mlflow.svc.cluster.local:9000',
    'experiment-name': 'cloud-hpc-pipeline',
    'model-name': 'fashion-mnist-cnn',
    'registered-name': 'FMNIST-CNN'
}

metric_parameters = {
    'accuracy': 0.80,
    'precision': 0.80,
    'recall': 0.80
}

pipeline_arguments = {
    'allas_parameters': allas_parameters,
    'ray_parameters': ray_parameters,
    'metadata_parameters': metadata_parameters,
    'mlflow_parameters': mlflow_parameters,
    'metric_parameters': metric_parameters
}