response = requests.get(
    url = 'http://127.0.0.1:5555/logs'
)
logs = json.loads(response.text)['porter-logs']
for log in logs:
    print(log)

response = requests.get(
    url = 'http://127.0.0.1:5556/logs'
)
logs = json.loads(response.text)['submitter-logs']
for log in logs:
    print(log)

slurm_artifacts = gather_slurm_artifacts(
    proxy_target = 'submitter',
    proxy_url = submitter_url,
    kubeflow_user = metadata_parameters['kubeflow-user'],
    slurm_job_id = '3472769',
)

with open('kubeflow_slurm_artifacts_0.json', 'w') as f:
    json.dump(slurm_artifacts[0], f, indent = 4)

with open('kubeflow_slurm_artifacts_1.json', 'w') as f:
    json.dump(slurm_artifacts[1], f, indent = 4)

with open('kubeflow_slurm_artifacts_2.txt', 'w') as file:
    for row in slurm_artifacts[2]:
        file.write(row + '\n')

ray_artifacts = gather_ray_artifacts(
    allas_client = allas_client,
    allas_bucket = allas_bucket,
    kubeflow_user = metadata_parameters['kubeflow-user'],
    ray_parameters = ray_parameters
)


with open('kubeflow_artifacts_1.json', 'w') as f:
    json.dump(ray_artifacts[1], f, indent = 4)

import torch
torch.save(ray_artifacts[2]['parameters']['model'], 'kubeflow_model.pth')

torch.save(ray_artifacts[2]['parameters']['optimizer'], 'kubeflow_optimizer.pth')

import numpy as np
np.save('kubeflow_predictions.npy',ray_artifacts[2]['predictions'])

kubeflow_metrics = get_object(
    client = allas_client,
    bucket_name = allas_bucket,
    object_path = 'EXPERIMENT/ARTIFACTS/kubeflow-metrics'
)

kubeflow_parameters = get_object(
    client = allas_client,
    bucket_name = allas_bucket,
    object_path = 'EXPERIMENT/ARTIFACTS/kubeflow-parameters'
)

job_parameters = ray_parameters['job-parameters']
data_folder_path = job_parameters['data-folder-path']
test_loader_path = data_folder_path + '/fmnist-test'
test_loader = get_object(
    client = allas_client,
    bucket_name = allas_bucket,
    object_path = test_loader_path
)

first_batch = next(iter(test_loader))
inputs, labels = first_batch
sample_inputs = inputs.numpy().tolist()
sample_labels = labels.numpy().tolist()

import torch.nn as nn
import torch.nn.functional as F

class CNNClassifier(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(1, 6, 5)
        self.pool = nn.MaxPool2d(2, 2)
        self.conv2 = nn.Conv2d(6, 16, 5)
        self.fc1 = nn.Linear(16 * 4 * 4, 120)
        self.fc2 = nn.Linear(120, 84)
        self.fc3 = nn.Linear(84, 10)

    def forward(self, x):
        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        x = x.view(-1, 16 * 4 * 4)
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = self.fc3(x)
        return x

def inference(
    model_state_path: any,
    inputs: any
) -> any:
    model = CNNClassifier()
    model.load_state_dict(torch.load(model_state_path))
    predictions = []
    inputs = torch.tensor(np.array(inputs, dtype=np.float32))
    with torch.no_grad():
        model.eval()
        outputs = model(inputs)
        preds = torch.max(outputs, 1)[1]
        predictions.extend(preds.tolist())
    return predictions

created_preds = inference(
    model_state_path = 'kubeflow_model.pth',
    inputs = sample_inputs
)

bridge_times = gather_bridge_times(
    allas_client = allas_client,
    allas_bucket = allas_bucket,
    kubeflow_user = metadata_parameters['kubeflow-user'],
    time_folder_path = metadata_parameters['time-folder-path']
)

with open('kubeflow_bridge_times.json', 'w') as f:
    json.dump(bridge_times, f, indent = 4)

submitter_times = gather_submitter_times(
    allas_client = allas_client,
    allas_bucket = allas_bucket,
    kubeflow_user = metadata_parameters['kubeflow-user']
)

with open('kubeflow_submitter_times.json', 'w') as f:
    json.dump(submitter_times, f, indent = 4)

with open('kubeflow_porter_times.json', 'w') as f:
    json.dump(porter_times, f, indent = 4)