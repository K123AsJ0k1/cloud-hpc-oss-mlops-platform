
import sys
import ray
import json

from functions.minio_os import minio_setup_client
from preprocessing.ray_step_1.functions.paths import fetch_repository_paths
from preprocessing.ray_step_1.functions.store import store_repository_documents
from functions.utility import divide_list

from importlib.metadata import version

def store_data(
    storage_parameters: any, 
    data_parameters: any
):
    try: 
        worker_number = process_parameters['worker-number']

        print('Creating minio client')
        object_client = minio_setup_client(
            endpoint = storage_parameters['minio-endpoint'],
            username = storage_parameters['minio-username'],
            password = storage_parameters['minio-password']
        )
        print('Minio client created')

        
        #github_token = data_parameters['github-token']
        #repository_owner = data_parameters['repository-owner']
        #repository_name = data_parameters['repository-name']
        #object_bucket = data_parameters['object-bucket']
        #repo_paths_object = data_parameters['repo-paths-object']
        #relevant_files = data_parameters['relevant-files']
        #replace = data_parameters['replace']

        #print('Getting repository paths')
        
        #repository_paths = fetch_repository_paths( 
        #    object_client = object_client,
        #    data_parameters = data_parameters
        #)

        #print('Amount of paths: ' + str(len(repository_paths)))
        #print('Dividing paths between ' + str(worker_number) + ' workers')

        #path_batches = divide_list(
        #    target_list = repository_paths,
        #    number = worker_number
        #)

        #print('Referencing paths')
        #path_batch_refs = []
        #for path_batch in path_batches:
        #    path_batch_refs.append(ray.put(path_batch))

        #print('Storing repository documents')
        #task_1_refs = []
        #for path_batch_ref in path_batch_refs:
        #    task_1_refs.append(store_repository_documents.remote(
        #        storage_parameters = storage_parameters,
        #        data_parameters = data_parameters,
        #        repository_paths = path_batch_ref 
        #    ))
        
        #remaining_task_1 = task_1_refs
        #task_1_outputs = []
        #while len(remaining_task_1):
        #    done, remaining_task_1 = ray.wait(remaining_task_1, num_returns = 1)
        #    output = ray.get(done[0])
        #    task_1_outputs.append(output)
        
        #print('Documents stored')
        
        return True
    except Exception as e:
        print('Fetch and store error')
        print(e)
        return False

if __name__ == "__main__":
    print('Starting ray job')
    print('Python version is:' + str(sys.version))
    print('Ray version is:' + version('Ray'))
    print('PyGithub version is:' + version('PyGithub'))
    print('PyMongo version is:' + version('PyMongo'))
    print('Markdown version is:' + version('Markdown'))
    print('Tree-sitter version is:' + version('tree-sitter'))
    print('Tree-sitter-python version is:' + version('tree-sitter-python'))
    print('BeautifulSoup version is:' + version('beautifulsoup4'))
    print('NBformat version is:' + version('nbformat'))
    
    input = json.loads(sys.argv[1])

    process_parameters = input['process-parameters']
    storage_parameters = input['storage-parameters']
    data_parameters = input['data-parameters']

    print('Running store data')

    store_data_status = store_data(
        process_parameters = process_parameters,
        storage_parameters = storage_parameters,
        data_parameters = data_parameters
    )
    
    print('Store data success:' + str(store_data_status))

    print('Ray job Complete')
