@dsl.pipeline(
    name = 'cloud-hpc-pipeline',
    description = 'Cloud-HPC integrated pipeline for Fashion MNIST CNN',
)
def pipeline(
    storage_parameters: dict,
    integration_parameters: dict,
    mlflow_parameters: dict,
    metric_parameters: dict
):
    preprocess_task = preprocess(
        storage_parameters = storage_parameters,
        integration_parameters = integration_parameters
    )

    preprocess_sucess = preprocess_task.output
    
    with dsl.Condition(preprocess_sucess == 'true'):
        train_task = train(
            storage_parameters = storage_parameters,
            integration_parameters = integration_parameters,
            mlflow_parameters = mlflow_parameters
        )
        train_task.after(preprocess_task)
        train_task.apply(use_aws_secret(secret_name="aws-secret"))

        with dsl.Condition(train_task.outputs["run_id"] != "none"):
            evaluate_task = evaluate(
                storage_parameters = storage_parameters,
                integration_parameters = integration_parameters,
                mlflow_parameters = mlflow_parameters,
                metric_parameters = metric_parameters,
                run_id = train_task.outputs["run_id"]
            )
            evaluate_task.after(train_task)