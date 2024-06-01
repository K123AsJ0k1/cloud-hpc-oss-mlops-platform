@dsl.pipeline(
    name = 'integration-pipeline',
    description = 'Cloud-HPC integrated pipeline for Fashion MNIST CNN',
)
def pipeline(
    allas_parameters: dict,
    ray_parameters: dict,
    metadata_parameters: dict,
    mlflow_parameters: dict,
    metric_parameters: dict
):
    preprocess_task = preprocess(
        allas_parameters = allas_parameters,
        ray_parameters = ray_parameters,
        metadata_parameters = metadata_parameters
    )

    preprocess_sucess = preprocess_task.output
    
    with dsl.Condition(preprocess_sucess == 'true'):
        train_task = train(
            allas_parameters = allas_parameters,
            ray_parameters = ray_parameters,
            metadata_parameters = metadata_parameters,
            mlflow_parameters = mlflow_parameters
        )
        train_task.after(preprocess_task)
        train_task.apply(use_aws_secret(secret_name="aws-secret"))

        with dsl.Condition(train_task.outputs["run_id"] != "none"):
            evaluate_task = evaluate(
                allas_parameters = allas_parameters,
                metadata_parameters = metadata_parameters,
                mlflow_parameters = mlflow_parameters,
                metric_parameters = metric_parameters,
                run_id = train_task.outputs["run_id"]
            )
            evaluate_task.after(train_task)

            clear_task = clear(
                allas_parameters = allas_parameters,
                metadata_parameters = metadata_parameters,
            )
            clear_task.after(evaluate_task)