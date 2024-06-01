from functions.slurm import format_sacct_command
from functions.pytorch import inference

resource_sacct_command = format_sacct_command(
    category = 'resource',
    job_id = '3440381'
)
print(resource_sacct_command)

time_sacct_command = format_sacct_command(
    category = 'time',
    job_id = '3440381'
)
print(time_sacct_command)

mahti_metrics = get_object(
    client = allas_client,
    bucket_name = allas_bucket,
    object_path = 'EXPERIMENT/ARTIFACTS/mahti-metrics'
)

with open('mahti_metrics.json', 'w') as f:
    json.dump(mahti_metrics, f, indent = 4)

mahti_parameters = get_object(
    client = allas_client,
    bucket_name = allas_bucket,
    object_path = 'EXPERIMENT/ARTIFACTS/mahti-parameters'
)

torch.save(mahti_parameters['model'], 'mahti_model.pth')

torch.save(mahti_parameters['optimizer'], 'mahti_optimizer.pth')

mahti_predictions = get_object(
    client = allas_client,
    bucket_name = allas_bucket,
    object_path = 'EXPERIMENT/ARTIFACTS/mahti-predictions'
)

np.save('mahti_predictions.npy',mahti_predictions)

created_preds = inference(
    model_state_path = 'mahti_model.pth',
    inputs = sample_inputs
)