import torch.nn as nn
import torch.nn.functional as F
import torchmetrics as TM

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