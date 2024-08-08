# Refactored
def wait_kubeflow_run(
    kfp_client: any,
    timeout: int,
    run_id: str
):
    start = t.time()
    run_status = None
    print('Checking kubeflow run: ' + str(run_id))
    while t.time() - start <= timeout:
        run_details = kfp_client.get_run(
            run_id = run_id
        )
        run_status = run_details.run.status
        print('Run status: ' + str(run_status))
        if run_status == 'Failed':
            run_status = False
            break
        if run_status == 'Succeeded':
            run_status = True
            break
        if run_status == 'Error':
            run_status = True
            break
        t.sleep(10)
    return run_status
# Created
def manage_kubeflow_run(
    submitter_file_paths: any,
    submitter_address: str,
    submitter_port: str,
    submitter_configuration: str,
    storage_client: any,
    storage_name: str,
    kfp_client: any,
    run_name: str,
    experiment_name: str,
    pipeline_arguments: any,
    timeout: int
):
    time_start = t.time()

    submitter_deployed = start_submitter(
        file_paths = submitter_file_paths,
        address = submitter_address,
        port = submitter_port,
        configuration = submitter_configuration
    )

    if submitter_deployed:
        print('Submitting pipeline')
        run_details = kfp_client.create_run_from_pipeline_func(
            pipeline_func = pipeline,
            run_name = run_name,
            experiment_name = experiment_name,
            arguments = pipeline_arguments,
            mode = kfp.dsl.PipelineExecutionMode.V2_COMPATIBLE,
            enable_caching = True,
            namespace = "kubeflow-user-example-com"
        )
    
        run_status = wait_kubeflow_run(
            kfp_client = kfp_client,
            timeout = timeout,
            run_id = run_details.run_id
        )
    
        print('Run status: ' + str(run_status))

    time_end = t.time()

    gather_time(
        storage_client = storage_client,
        storage_name = storage_name,
        time_group = 'components',
        time_name = 'cloud-hpc-pipeline',
        start_time = time_start,
        end_time = time_end
    )

    print('Kubeflow pipeline complete')