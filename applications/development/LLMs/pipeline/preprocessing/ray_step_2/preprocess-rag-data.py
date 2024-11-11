
import sys
import ray
import json

from functions.mongo_db import mongo_setup_client
from functions.minio_os import minio_setup_client

from functions.get_documents import get_stored_documents

from functions.embeddings import store_embeddings
from functions.keywords import store_keywords
from functions.utility import divide_list, get_checked_documents, get_github_storage_prefix, store_checked_documents

from importlib.metadata import version

  
def preprocess_data(
    process_parameters: any,
    storage_parameters: any,
    data_parameters: any
):
    try:
        worker_number = process_parameters['worker-number']
        
        print('Creating mongo client')
        mongo_client = mongo_setup_client(
            username = storage_parameters['mongo-username'],
            password = storage_parameters['mongo-password'],
            address = storage_parameters['mongo-address'],
            port = storage_parameters['mongo-port']
        )
        print('Mongo client created')

        print('Creating minio client')
        minio_client = minio_setup_client(
            endpoint = storage_parameters['minio-endpoint'],
            username = storage_parameters['minio-username'],
            password = storage_parameters['minio-password']
        )
        print('Minio client created')

        repository_owner = data_parameters['repository-owner']
        repository_name = data_parameters['repository-name']
        configuration = data_parameters['configuration']

        print('Getting stored documents')
        
        stored_documents = get_stored_documents(
            document_client = mongo_client,
            database_prefix = get_github_storage_prefix(
                repository_owner = repository_owner,
                repository_name = repository_name
            )
        )

        print('Dividing documents for ' + str(worker_number) + ' workers')

        divided_documents = divide_list(
            target_list = stored_documents,
            number = worker_number
        )

        print('Referencing documents')

        doc_refs = []
        for docs in divided_documents:
            doc_refs.append(ray.put(docs))

        print('Getting vector ids')

        vector_ids = get_checked_documents(
            object_client = minio_client,
            configuration = configuration,
            prefix = configuration['vector-prefix']
        )

        print('Referencing vector ids')

        vector_ids_ref = ray.put(vector_ids)

        print('Running store embeddings')
        task_refs = []
        for doc_ref in doc_refs:
            task_refs.append(store_embeddings.remote(
                storage_parameters = storage_parameters,
                configuration = configuration,
                storage_documents = doc_ref,
                given_identities = vector_ids_ref
            ))
        task_outputs = ray.get(task_refs)
        print('Outputs received')

        updated_vector_ids = sum(task_outputs,[])

        print('Storing vector ids')
        store_checked_documents(
            object_client = minio_client,
            configuration = configuration,
            prefix = configuration['vector-prefix'],
            checked_documents = updated_vector_ids
        )

        print('Getting search ids')
        
        search_ids = get_checked_documents(
            object_client = minio_client,
            configuration = configuration,
            prefix = configuration['search-prefix']
        )

        print('Referencing search ids')

        search_ids_ref = ray.put(search_ids)

        print('Running store keywords')
        task_refs = []
        for doc_ref in doc_refs:
            task_refs.append(store_keywords.remote(
                storage_parameters = storage_parameters,
                configuration = configuration,
                storage_documents = doc_ref,
                given_identities = search_ids_ref
            ))
        task_outputs = ray.get(task_refs)
        print('Outputs received')

        updated_search_ids = sum(task_outputs,[])

        print('Storing search ids')
        store_checked_documents(
            object_client = minio_client,
            configuration = configuration,
            prefix = configuration['search-prefix'],
            checked_documents = updated_search_ids
        )
        
        return True
    except Exception as e:
        print('Preprocess error')
        print(e)
        return False

if __name__ == "__main__":
    print('Starting ray job')
    print('Python version is:' + str(sys.version))
    print('Ray version is:' + version('ray'))
    print('PyMongo version is:' + version('pymongo'))
    print('Qdrant version is:' + version('qdrant-client'))
    print('Meilisearch version is:' + version('meilisearch'))
    print('Langchain version is:' + version('langchain'))
    print('Langchain huggingface version is:' + version('langchain-huggingface'))
    print('Spacy version is:' + version('spacy'))
    
    input = json.loads(sys.argv[1])

    process_parameters = input['process-parameters']
    storage_parameters = input['storage-parameters']
    data_parameters = input['data-parameters']

    print('Running preprocess')

    preprocess_status = preprocess_data(
        process_parameters = process_parameters,
        storage_parameters = storage_parameters,
        data_parameters = data_parameters
    )
    
    print('Preprocess success:' + str(preprocess_status))

    print('Ray job Complete')
