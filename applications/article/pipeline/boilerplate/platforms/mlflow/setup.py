def setup_mlflow(
    logger: any,
    mlflow_parameters: any
):
    mlflow_s3_endpoint_url = mlflow_parameters['s3-endpoint-url']
    mlflow_tracking_uri = mlflow_parameters['tracking-uri']
    mlflow_experiment_name = mlflow_parameters['experiment-name']
    
    os.environ['MLFLOW_S3_ENDPOINT_URL'] = mlflow_s3_endpoint_url

    logger.info(f"Using MLflow tracking URI: {mlflow_tracking_uri}")
    mlflow.set_tracking_uri(mlflow_tracking_uri)
    logger.info(f"Using MLflow experiment: {mlflow_experiment_name}")
    mlflow.set_experiment(mlflow_experiment_name)