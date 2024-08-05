import sys

import ray
import swiftclient as sc
import pickle
import json
import time as t

import torch
import torch.nn as nn
import torch.nn.functional as F
import torchmetrics as TM

# Allas 
def setup_allas(
    parameters: any
) -> any:
    allas_client = sc.Connection(
        preauthurl = parameters['pre_auth_url'],
        preauthtoken = parameters['pre_auth_token'],
        os_options = {
            'user_domain_name': parameters['user_domain_name'],
            'project_domain_name': parameters['project_domain_name'],
            'project_name': parameters['project_name']
        },
        auth_version = parameters['auth_version']
    )
    return allas_client

def create_bucket(
    client: any,
    bucket_name: str
) -> bool:
    try:
        client.put_container(
            container = bucket_name
        )
        return True
    except Exception as e:
        return False

def check_bucket(
    client: any,
    bucket_name:str
) -> bool:
    try:
        container_info = client.get_container(
            container = bucket_name
        )
        return container_info
    except Exception as e:
        return None 
    
def create_object(
    client: any,
    bucket_name: str, 
    object_path: str, 
    data: any
) -> bool: 
    try:
        client.put_object(
            container = bucket_name,
            obj = object_path + '.pkl',
            contents = pickle.dumps(data),
            content_type = 'application/pickle'
        )
        return True
    except Exception as e:
        return False
    
def check_object(
    client: any,
    bucket_name: str, 
    object_path: str
) -> any: 
    try:
        object_info = client.head_object(
            container = bucket_name,
            obj = object_path + '.pkl'
        )       
        return object_info
    except Exception as e:
        return {} 

def get_object(
    client:any,
    bucket_name: str,
    object_path: str
) -> any:
    try:
        content = client.get_object(
            container = bucket_name,
            obj = object_path + '.pkl' 
        )
        data = pickle.loads(content[1])
        return data
    except Exception as e:
        return None     
    
def remove_object(
    client: any,
    bucket_name: str, 
    object_path: str
) -> bool: 
    try:
        client.delete_object(
            container = bucket_name, 
            obj = object_path + '.pkl'
        )
        return True
    except Exception as e:
        return False

def update_object(
    client: any,
    bucket_name: str, 
    object_path: str, 
    data: any,
) -> bool:  
    remove = remove_object(
        client, 
        bucket_name, 
        object_path
    )
    if remove:
        create = create_object(
            client, 
            bucket_name, 
            object_path, 
            data
        )
        if create:
            return True
    return False

def create_or_update_object(
    client: any,
    bucket_name: str, 
    object_path: str, 
    data: any
) -> any:
    bucket_status = check_bucket(
        client, 
        bucket_name
    )
    
    if not bucket_status:
        creation_status = create_bucket(
            client, 
            bucket_name
        )
        if not creation_status:
            return False
    
    object_status = check_object(
        client, 
        bucket_name, 
        object_path
    )
    
    if not object_status:
        return create_object(
            client, 
            bucket_name, 
            object_path, 
            data
        )
    else:
        return update_object(
            client, 
            bucket_name, 
            object_path, 
            data
        )

def gather_time(
    allas_client: any,
    allas_bucket: str,
    kubeflow_user: str,
    time_folder_path: str,
    object_name: str,
    action_name: str,
    start_time: int,
    end_time: int
):
    time_path = time_folder_path + '/' + object_name
    current_data = get_object(
        client = allas_client,
        bucket_name = allas_bucket,
        object_path = time_path
    )

    object_data = None
    if current_data is None:
        object_data = {}
    else:
        object_data = current_data

    if not kubeflow_user in object_data:
        object_data[kubeflow_user] = {}

    user_time_dict = object_data[kubeflow_user]

    current_key_amount = len(user_time_dict)
    current_key_full = False
    current_key = str(current_key_amount)
    if 0 < current_key_amount:
        time_object = user_time_dict[current_key]
        if 0 < time_object['total-seconds']:
            current_key_full = True
    
    changed = False
    if 0 < end_time and 0 < current_key_amount and not current_key_full:
        stored_start_time = user_time_dict[current_key]['start-time']
        time_diff = (end_time-stored_start_time)
        user_time_dict[current_key]['end-time'] = end_time
        user_time_dict[current_key]['total-seconds'] = round(time_diff,5)
        changed = True
    else:
        next_key_amount = len(user_time_dict) + 1
        new_key = str(next_key_amount)
    
        if 0 < start_time and 0 == end_time:
            user_time_dict[new_key] = {
                'name': action_name,
                'start-time': start_time ,
                'end-time': 0,
                'total-seconds': 0
            }
            changed = True

        if 0 < start_time and 0 < end_time:
            time_diff = (end_time-start_time)
            user_time_dict[new_key] = {
                'name': action_name,
                'start-time': start_time,
                'end-time': end_time,
                'total-seconds': round(time_diff,5)
            }
            changed = True

    if changed:
        object_data[kubeflow_user] = user_time_dict
        create_or_update_object(
            client = allas_client,
            bucket_name = allas_bucket,
            object_path = time_path, 
            data = object_data
        )      
# Pytorch 
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

def get_general_metrics():
    general_metrics = TM.MetricCollection([
        TM.classification.MulticlassAccuracy(
            num_classes = 10,
            average = 'macro'
        ),
        TM.classification.MulticlassPrecision(
            num_classes = 10,
            average = 'macro'
        ),
        TM.classification.MulticlassRecall(
            num_classes = 10,
            average = 'macro'
        )
    ])
    return general_metrics
    
def get_class_metrics():
    class_metrics = TM.MetricCollection([
        TM.classification.MulticlassAccuracy(
            num_classes = 10,
            average = None
        ),
        TM.classification.MulticlassPrecision(
            num_classes = 10,
            average = None
        ),
        TM.classification.MulticlassRecall(
            num_classes = 10,
            average = None
        )
    ])
    return class_metrics
    
@ray.remote
def remote_model_training(
    allas_client: any,
    allas_bucket: any,
    kubeflow_user: str,
    artifact_path: str,
    time_folder_path: str,
    seed: int,
    train_print_rate: int,
    epochs: int,
    learning_rate: float,
    momentum: float,
    train_loader: any,
    test_loader: any
):
    try:
        time_start = t.time()
    
        print('Defining model')
        model = CNNClassifier()
        criterion = torch.nn.CrossEntropyLoss()
        optimizer = torch.optim.SGD(
            model.parameters(), 
            lr = learning_rate, 
            momentum = momentum
        )
        torch.manual_seed(seed)
    
        print('Defining metrics')
        general_metrics = get_general_metrics()
        class_metrics = get_class_metrics()
        
        print('Starting model training')
        current_epoch = 0
        for epoch in range(epochs):
            running_loss = 0.0
            model.train()
            for i, data in enumerate(train_loader):
                inputs, labels = data
                optimizer.zero_grad()
                outputs = model(inputs)
                
                loss = criterion(outputs, labels)
                
                loss.backward()
                optimizer.step()
                running_loss += loss.item()
    
                preds = torch.max(outputs, 1)[1]
        
                general_metrics(preds, labels)
                
                if (i + 1) % train_print_rate == 0:
                    avg_loss = running_loss / train_print_rate
                    train_general_metrics = general_metrics.compute()
                    acc = round(train_general_metrics['MulticlassAccuracy'].item(),3)
                    pre = round(train_general_metrics['MulticlassPrecision'].item(),3)
                    rec = round(train_general_metrics['MulticlassRecall'].item(),3)
                    general_metrics.reset()
                    print(f'Epoch: {epoch + 1}/{epochs}, Batch {i + 1}, Loss: {avg_loss}, Accuracy: {acc}, Precision: {pre}, Recall: {rec}')
                    running_loss = 0.0
            current_epoch += 1
        print('Training complete')
        
        general_metrics.reset()
        
        print('Starting model testing')
        running_loss = 0.0
        predictions = []
        with torch.no_grad():
            model.eval()
            for i, data in enumerate(test_loader):
                inputs, labels = data
                outputs = model(inputs)
                preds = torch.max(outputs, 1)[1]
                loss = criterion(outputs, labels)
                general_metrics(preds, labels)
                class_metrics(preds, labels)
                predictions.extend(preds.tolist())
                running_loss += loss.item()
        print('Testing complete')
    
        print('Storing created artifacts')
        
        test_general_metrics = general_metrics.compute()
        test_class_metrics = class_metrics.compute()
    
        general_metrics.reset()
        class_metrics.reset()
    
        predictions_path = artifact_path + '-predictions'
        print('Predictions object path:' + str(predictions_path))
        predictions_status = create_or_update_object(
            client = allas_client,
            bucket_name = allas_bucket,
            object_path = predictions_path,
            data = predictions
        )
        print('Prediction storing status:' + str(predictions_status))
        
        print('Formatting model parameters')
        model_parameters = model.state_dict()
        optimizer_parameters = optimizer.state_dict()
    
        parameters = {
            'epoch': current_epoch,
            'model': model_parameters,
            'optimizer': optimizer_parameters
        }
    
        parameters_path = artifact_path + '-parameters'
        print('Parameters object path:' + str(parameters_path))
        storing_status = create_or_update_object(
            client = allas_client,
            bucket_name = allas_bucket,
            object_path = parameters_path,
            data = parameters
        )
        print('Parameters storing status:' + str(storing_status))
    
        print('Formatting model metrics')
        accuracy = test_general_metrics['MulticlassAccuracy'].item()
        precision = test_general_metrics['MulticlassPrecision'].item()
        recall = test_general_metrics['MulticlassRecall'].item()
    
        class_accuracy = test_class_metrics['MulticlassAccuracy'].tolist()
        class_precision = test_class_metrics['MulticlassPrecision'].tolist()
        class_recall = test_class_metrics['MulticlassRecall'].tolist()
    
        metrics = {
            'name': 'Convolutional-neural-network-classifier',
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'class-accuracy': class_accuracy,
            'class-precision': class_precision,
            'class-recall': class_recall
        }
    
        metrics_path = artifact_path + '-metrics'
        print('Predictions object path:' + str(metrics_path))
        storing_status = create_or_update_object(
            client = allas_client,
            bucket_name = allas_bucket,
            object_path = metrics_path,
            data = metrics
        )
        print('Metrics storing status:' + str(storing_status))

        time_end = t.time()

        time_end = t.time()
        time_diff = (time_end - time_start) 
        
        exp_time = {
            'name': 'ray-model-training',
            'start-time': time_start,
            'end-time': time_end,
            'total-seconds': round(time_diff,5)
        }

        exp_metrics = {
            'performance': metrics,
            'time': exp_time
        }

        exp_metrics_path = artifact_path + '-metrics'
        print('Metrics object path:' + str(exp_metrics_path))
        storing_status = create_or_update_object(
            client = allas_client,
            bucket_name = allas_bucket,
            object_path = exp_metrics_path,
            data = exp_metrics
        )
        print('Metrics storing status:' + str(storing_status))
    
        gather_time(
            allas_client = allas_client,
            allas_bucket =  allas_bucket,
            kubeflow_user = kubeflow_user,
            time_folder_path = time_folder_path,
            object_name = 'ray-job',
            action_name = 'remote-model-training',
            start_time = time_start,
            end_time = time_end
        )

        return True
    except Exception as e:
        print(e)
        return False

if __name__ == "__main__":
    print('Starting ray job')
    print('Ray version is:' + str(ray.__version__))
    print('Swiftclient version is:' + str(sc.__version__))
    print('Torch version is:' + str(torch.__version__))
    print('Torchmetrics version is:' + str(TM.__version__))
    time_start = t.time()
    
    input = json.loads(sys.argv[1])
    print('Setting Allas client')
    allas_parameters = input['allas-parameters']
    allas_client = setup_allas(
        parameters = allas_parameters
    )
    allas_bucket = allas_parameters['allas-bucket']
    print('Allas client setup')

    job_parameters = input['job-parameters']
    data_folder_path = job_parameters['data-folder-path']
    kubeflow_user = job_parameters['kubeflow-user']
    artifact_path = job_parameters['artifact-path']
    time_folder_path = job_parameters['time-folder-path']
    train_print_rate = job_parameters['train-print-rate']
    seed = job_parameters['hp-seed']
    epochs = job_parameters['hp-epochs']
    learning_rate = job_parameters['hp-learning-rate']
    momentum = job_parameters['hp-momentum']

    print('Getting data')
    
    train_loader_path = data_folder_path + '/fmnist-train'
    print('Train loader path: ' + str(train_loader_path))
    train_loader = get_object(
        client = allas_client,
        bucket_name = allas_bucket,
        object_path = train_loader_path
    )
    test_loader_path = data_folder_path + '/fmnist-test'
    print('Test loader path: ' + str(test_loader_path))
    test_loader = get_object(
        client = allas_client,
        bucket_name = allas_bucket,
        object_path = test_loader_path
    )
    print('Data loaded')

    print('Training')
    
    training_status = ray.get(remote_model_training.remote(
        allas_client = allas_client,
        allas_bucket = allas_bucket,
        kubeflow_user = kubeflow_user,
        artifact_path = artifact_path,
        time_folder_path = time_folder_path,
        seed = seed,
        train_print_rate = train_print_rate,
        epochs = epochs,
        learning_rate = learning_rate,
        momentum = momentum,
        train_loader = train_loader,
        test_loader = train_loader
    ))

    time_end = t.time()

    gather_time(
        allas_client = allas_client,
        allas_bucket =  allas_bucket,
        kubeflow_user = kubeflow_user,
        time_folder_path = time_folder_path,
        object_name = 'ray-job',
        action_name = 'exp-train',
        start_time = time_start,
        end_time = time_end
    )

    print('Training success:' + str(training_status))
    print('Ray job Complete')