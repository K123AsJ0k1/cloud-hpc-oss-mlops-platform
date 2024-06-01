import time as t
import logging

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

def submit_pipeline(
    submitter_parameters: any,
    submitter_url: str,
    porter_url: str,
    run_name: str,
    experiment_name: str,
    pipeline_arguments: any,
    kubeflow_run_timeout: int
): 
    time_start = t.time()
    
    allas_parameters = pipeline_arguments['allas_parameters']

    allas_client = setup_allas(
        parameters = allas_parameters
    )
    allas_bucket = allas_parameters['allas-bucket']
    print('Allas client setup')

    kubeflow_user = pipeline_arguments['metadata_parameters']['kubeflow-user']
    time_folder_path = pipeline_arguments['metadata_parameters']['time-folder-path']
    
    setup = setup_proxy(
        proxy_parameters = submitter_parameters,
        proxy_url = submitter_url
    )

    if setup:
        started = start_proxy(
            proxy_url = submitter_url
        )
        print('Submitter setup: ' + str(started))

        if started:
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
            print('Pipeline submitted')
            
            run_status = wait_kubeflow_run(
                kfp_client = kfp_client,
                timeout = kubeflow_run_timeout,
                run_id = run_details.run_id
            )
            print('Run status: ' + str(run_status))
            if not run_status:
                porter_stopped = stop_proxy(
                    proxy_url = porter_url
                )
                print('Porter stopped: ' + str(porter_stopped))

            stopped = stop_proxy(
                proxy_url = submitter_url
            )

            print('Submitter stopped: ' + str(stopped))
        
    time_end = t.time()

    gather_time(
        allas_client = allas_client,
        allas_bucket =  allas_bucket,
        kubeflow_user = kubeflow_user,
        time_folder_path = time_folder_path,
        object_name = 'workflow',
        action_name = 'kubeflow-pipeline',
        start_time = time_start,
        end_time = time_end
    )
    print('Kubeflow pipeline complete')