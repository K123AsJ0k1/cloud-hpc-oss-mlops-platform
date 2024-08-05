import logging

from functions.gather import gather_slurm_artifacts,gather_ray_artifacts

logging.basicConfig(level = logging.INFO)
logger = logging.getLogger(__name__)

response = requests.get(
    url = 'http://127.0.0.1:5556/logs'
)
logs = json.loads(response.text)['submitter-logs']
for log in logs:
    print(log)

slurm_artifacts = gather_slurm_artifacts(
    logger = logger,
    proxy_target = metadata_parameters['proxy-target'],
    proxy_url = metadata_parameters['proxy-url'],
    kubeflow_user = metadata_parameters['kubeflow-user'],
    slurm_job_id = '3457415',
)

with open('ray_slurm_artifacts_0.json', 'w') as f:
    json.dump(slurm_artifacts[0], f, indent = 4)

with open('ray_slurm_artifacts_1.json', 'w') as f:
    json.dump(slurm_artifacts[1], f, indent = 4)

with open('ray_slurm_artifacts_2.txt', 'w') as file:
    for row in slurm_artifacts[2]:
        file.write(row + '\n')

logging.basicConfig(level = logging.INFO)
logger = logging.getLogger(__name__)

ray_artifacts = gather_ray_artifacts(
    logger = logger,
    allas_client = allas_client,
    allas_bucket = allas_bucket,
    kubeflow_user = metadata_parameters['kubeflow-user'],
    ray_parameters = ray_parameters
)

ray_artifacts[1]

with open('ray_artifacts_1.json', 'w') as f:
    json.dump(ray_artifacts[1], f, indent = 4)

torch.save(ray_artifacts[2]['parameters']['model'], 'ray_model.pth')

torch.save(ray_artifacts[2]['parameters']['optimizer'], 'ray_optimizer.pth')

np.save('ray_predictions.npy',ray_artifacts[2]['predictions'])

ray_metrics = get_object(
    client = allas_client,
    bucket_name = allas_bucket,
    object_path = 'EXPERIMENT/ARTIFACTS/ray-metrics'
)

ray_parameters = get_object(
    client = allas_client,
    bucket_name = allas_bucket,
    object_path = 'EXPERIMENT/ARTIFACTS/ray-parameters'
)

ray_predictions = get_object(
    client = allas_client,
    bucket_name = allas_bucket,
    object_path = 'EXPERIMENT/ARTIFACTS/ray-predictions'
)

first_batch = next(iter(test_loader))
inputs, labels = first_batch
sample_inputs = inputs.numpy().tolist()
sample_labels = labels.numpy().tolist()

created_preds = inference(
    model_state_path = 'ray_model.pth',
    inputs = sample_inputs
)

bridge_times = gather_bridge_times(
    allas_client = allas_client,
    allas_bucket = allas_bucket,
    kubeflow_user = metadata_parameters['kubeflow-user'],
    time_folder_path = metadata_parameters['time-folder-path']
)

with open('bridge_times.json', 'w') as f:
    json.dump(bridge_times, f, indent = 4)

submitter_times = gather_submitter_times(
    allas_client = allas_client,
    allas_bucket = allas_bucket,
    kubeflow_user = metadata_parameters['kubeflow-user']
)

with open('submitter_times.json', 'w') as f:
    json.dump(submitter_times, f, indent = 4)