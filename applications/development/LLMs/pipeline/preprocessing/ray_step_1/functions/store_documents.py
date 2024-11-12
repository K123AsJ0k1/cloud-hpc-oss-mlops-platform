

import ray

from functions.mongo_db import mongo_setup_client
from functions.pygithub import pygithub_get_path_contents
from functions.mongo_db import mongo_check_collection, mongo_create_document
from functions.create_documents import create_markdown_documents, create_python_documents, create_notebook_documents, create_yaml_documents
from functions.utility import divide_list, get_path_database_and_collection

def store_path_documents(
    mongo_client: any,
    database_name: str,
    collection_name: str,
    repository_path: str,
    path_content: any
):
    path_split = repository_path.split('/')
    path_type = path_split[-1].split('.')[-1]
    
    path_documents = {}
    if path_type == 'md':
        try:
            path_documents = create_markdown_documents(
                markdown_text = path_content
            )
        except Exception as e:
            print('Create markdown document error with path: ' + str(repository_path))
            print(e)

    if path_type == 'yaml':
        try:
            path_documents = create_yaml_documents(
                yaml_text = path_content
            )
        except Exception as e: 
            print('Create yaml document error with path: ' + str(repository_path))
            print(e)

    if path_type == 'py':
        try:
            path_documents = create_python_documents(
                python_text = path_content
            )
        except Exception as e:
            print('Create python document error with path: ' + str(repository_path))
            print(e)

    if path_type == 'ipynb':
        try:
            path_documents = create_notebook_documents(
                notebook_text = path_content
            )
        except Exception as e:
            print('Create notebook document error with path: ' + str(repository_path))
            print(e)
    
    if 0 < len(path_documents):
        for doc_type, docs in path_documents.items():
            for document in docs:
                result = mongo_create_document(
                    mongo_client = mongo_client,
                    database_name = database_name,
                    collection_name = collection_name,
                    document = document
                )
        return True
    return False

@ray.remote(
    num_cpus = 1,
    memory = 5 * 1024 * 1024 * 1024
)
def store_repository_documents(
    storage_parameters: any,
    data_parameters: any,
    repository_paths: any
) -> bool:
    print('Storing ' + str(len(repository_paths)) + ' repository documents')
    document_client = mongo_setup_client(
        username = storage_parameters['mongo-username'],
        password = storage_parameters['mongo-password'],
        address = storage_parameters['mongo-address'],
        port = storage_parameters['mongo-port']
    )

    github_token = data_parameters['github-token']
    repository_owner = data_parameters['repository-owner']
    repository_name = data_parameters['repository-name']
    batch_number = data_parameters['batch-number']

    divided_paths = divide_list(
        target_list = repository_paths,
        number = batch_number
    )
    stored = False
    for path_batch in divided_paths:
        print('Batch size: ' + str(len(path_batch)))
        new_paths = []
        for path in path_batch:
            database_name, collection_name = get_path_database_and_collection(
                repository_owner = repository_owner,
                repository_name = repository_name,
                path = path
            )
            
            collection_exists = mongo_check_collection(
                mongo_client = document_client, 
                database_name = database_name, 
                collection_name = collection_name
            )

            if not collection_exists:
                new_paths.append(path)
        
        print('New paths: ' + str(len(new_paths)))
        if 0 < len(new_paths):
            contents = []
            try:
                contents = pygithub_get_path_contents(
                    token = github_token,
                    owner = repository_owner, 
                    name = repository_name, 
                    paths = new_paths
                )
            except Exception as e:
                print('PyGithub error')
                print(e)

            contents_index = 0
            for path in new_paths:
                database_name, collection_name = get_path_database_and_collection(
                    repository_owner = repository_owner,
                    repository_name = repository_name,
                    path = path
                )

                stored = store_path_documents(
                    mongo_client = document_client,
                    database_name = database_name,
                    collection_name = collection_name,
                    repository_path = path,
                    path_content = contents[contents_index]
                )

                contents_index += 1
    return stored
