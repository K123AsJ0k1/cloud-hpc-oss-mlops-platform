from functions.pytorch import inference

created_artifacts['metrics']

torch.save(created_artifacts['parameters']['model'], 'local_model.pth')

torch.save(created_artifacts['parameters']['optimizer'], 'local_optimizer.pth')

first_batch = next(iter(test_loader))
inputs, labels = first_batch
sample_inputs = inputs.numpy().tolist()
sample_labels = labels.numpy().tolist()

created_preds = inference(
    model_state_path = 'local_model.pth',
    inputs = sample_inputs
)