

import ray

import uuid

from functions.documents import get_sorted_documents
from functions.mongo_db import mongo_setup_client

from functions.spacy import spacy_find_keywords
from functions.meili_sb import meili_setup_client,meili_add_documents, meili_set_filterable

def generate_keyword_uuid(
    document_id: str,
    document_index: int
) -> str:
    keyword_id = document_id + '-' + str(document_index + 1)
    keyword_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, keyword_id))
    return keyword_uuid

def create_document_keywords(
    database: str,
    collection: str,
    document: any,
    document_index: int
) -> any:
    document_id = str(document['_id'])
    document_data = document['data']
    document_type = document['type']

    document_keywords = []
    try:
        document_keywords = spacy_find_keywords(
            text = document_data
        )
    except Exception as e:
        print(e)

    if 0 == len(document_keywords):
        return {}
    
    keyword_uuid = generate_keyword_uuid(
        document_id = document_id,
        document_index = document_index
    ) 

    keyword_payload = {
        'id': keyword_uuid,
        'database': database,
        'collection': collection,
        'document': document_id,
        'type': document_type,
        'keywords': document_keywords
    }

    return keyword_payload

@ray.remote(
    num_cpus = 1,
    memory = 4 * 1024 * 1024 * 1024
) 
def store_keywords(
    storage_parameters: any,
    data_parameters: any,
    collection_tuples: any,
    given_identities: any
):
    document_client = mongo_setup_client(
        username = storage_parameters['mongo-username'],
        password = storage_parameters['mongo-password'],
        address = storage_parameters['mongo-address'],
        port = storage_parameters['mongo-port']
    )

    all_collections = len(collection_tuples)
    
    print('Storing keywords of ' + str(all_collections) + ' collections')

    search_client = meili_setup_client(
        api_key = storage_parameters['meili-key'],
        host = storage_parameters['meili-host']
    )
    
    collection_prefix = storage_parameters['search-collection-prefix']
    document_identities = given_identities
    document_index = len(document_identities)
    collection_index = 0
    for collection_tuple in collection_tuples:
        document_database = collection_tuple[0]
        document_collection = collection_tuple[1]
        
        collection_documents = get_sorted_documents(
            document_client = document_client,
            database = document_database,
            collection = document_collection
        ) 

        if collection_index % data_parameters['search-collection-print'] == 0:
            print(str(collection_index) + '/' + str(all_collections))
        collection_index += 1
    
        for document in collection_documents:
            search_collection = document_database.replace('|','-') + '-' + collection_prefix
            document_identity = document_database + '-' + document_collection + '-' + str(document['_id'])

            if document_identity in document_identities:
                continue
        
            document_keywords = create_document_keywords(
                database = document_database,
                collection = document_collection,
                document = document,
                document_index = document_index
            )
        
            if 0 < len(document_keywords):
                stored = meili_add_documents(
                    meili_client = search_client,
                    index_name = search_collection,
                    documents = document_keywords
                )

                meili_set_filterable(
                    meili_client = search_client, 
                    index_name = search_collection, 
                    attributes = ['keywords']
                )
                
                document_identities.append(document_identity)
            document_index += 1
    return document_identities
