import torch
import time as t

from functions.pytorch import CNNClassifier, get_general_metrics, get_class_metrics

def local_model_training(
    seed: int,
    train_print_rate: int,
    epochs: int,
    learning_rate: float,
    momentum: float,
    train_loader: any,
    test_loader: any
):
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

    test_general_metrics = general_metrics.compute()
    test_class_metrics = class_metrics.compute()

    general_metrics.reset()
    class_metrics.reset()

    print('Formatting created model')
    model_parameters = model.state_dict()
    optimizer_parameters = optimizer.state_dict()

    parameters = {
        'epoch': current_epoch,
        'model': model_parameters,
        'optimizer': optimizer_parameters
    }

    print('Formatting model metrics')
    accuracy = test_general_metrics['MulticlassAccuracy'].item()
    precision = test_general_metrics['MulticlassPrecision'].item()
    recall = test_general_metrics['MulticlassRecall'].item()

    class_accuracy = test_class_metrics['MulticlassAccuracy'].tolist()
    class_precision = test_class_metrics['MulticlassPrecision'].tolist()
    class_recall = test_class_metrics['MulticlassRecall'].tolist()

    performance = {
        'name': 'Convolutional-neural-network-classifier',
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'class-accuracy': class_accuracy,
        'class-precision': class_precision,
        'class-recall': class_recall
    }

    print('Formatting used time')

    time_end = t.time()
    time_diff = (time_end - time_start) 

    time = {
        'name': 'local-model-training',
        'start-time': time_start,
        'end-time': time_end,
        'total-seconds': round(time_diff,5)
    }

    metrics = {
        'performance': performance,
        'time': time
    }

    artifacts = {
        'metrics': metrics,
        'parameters': parameters,
        'predictions': predictions
    }
    print('Complete')
    return artifacts

created_artifacts = local_model_training(
    seed = 42,
    train_print_rate = 2000,
    epochs = 5,
    learning_rate = 0.001,
    momentum = 0.9,
    train_loader = train_loader,
    test_loader = test_loader
)
