@dsl.pipeline(
    name = 'cloud-pipeline',
    description = 'Cloud pipeline for Fashion MNIST CNN',
)
def pipeline(
    storage_parameters: dict,
    training_parameters: dict,
    mlflow_parameters: dict,
    metric_parameters: dict
):
    
    preprocess_train_task = preprocess_train(
        storage_parameters = storage_parameters,
        training_parameters = training_parameters,
        mlflow_parameters = mlflow_parameters 
    )
    preprocess_train_task.apply(use_aws_secret(secret_name="aws-secret"))

    with dsl.Condition(preprocess_train_task.outputs["run_id"] != "none"):
        evaluate_task = evaluate(
            storage_parameters = storage_parameters,
            mlflow_parameters = mlflow_parameters,
            metric_parameters = metric_parameters,
            run_id = preprocess_train_task.outputs["run_id"]
        )
        evaluate_task.after(preprocess_train_task)