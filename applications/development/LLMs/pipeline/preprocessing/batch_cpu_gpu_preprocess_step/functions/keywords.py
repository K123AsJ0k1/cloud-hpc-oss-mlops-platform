

import ray

from functions.utility import generate_uuid
from functions.documents import get_sorted_documents
from functions.mongo_db import mongo_setup_client
from functions.meili_sb import meili_setup_client,meili_add_documents, meili_set_filterable

def create_document_keywords( 
    actor_ref: any,
    database: str,
    collection: str,
    document: any,
    index: int
) -> any:
    id = str(document['_id'])
    type = document['type']
    data = document['data']

    keywords = []
    try:
        # Reduce actor reguests
        # by making this do batches 
        # make this also use wait 
        keywords = ray.get(actor_ref.find_keywords.remote(
            text = data
        ))
    except Exception as e:
        print(e)

    if 0 == len(keywords):
        return {}
    
    keyword_uuid = generate_uuid(
        id = id,
        index = index
    ) 

    keyword_payload = {
        'id': keyword_uuid,
        'database': database,
        'collection': collection,
        'document': id,
        'type': type,
        'keywords': keywords
    }

    return keyword_payload

@ray.remote(
    num_cpus = 1,
    memory = 4 * 1024 * 1024 * 1024
) 
def store_keywords(
    actor_ref: any,
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

    collection_amount = len(collection_tuples)
    
    print('Storing keywords of ' + str(collection_amount) + ' collections')

    search_client = meili_setup_client(
        api_key = storage_parameters['meili-key'],
        host = storage_parameters['meili-host']
    )
    
    collection_prefix = storage_parameters['search-collection-prefix']
    document_identities = given_identities
    document_index = len(document_identities)
    collection_number = 1
    for collection_tuple in collection_tuples:
        document_database = collection_tuple[0]
        document_collection = collection_tuple[1]
        
        collection_documents = get_sorted_documents(
            document_client = document_client,
            database = document_database,
            collection = document_collection
        ) 

        if collection_number % data_parameters['search-collection-print'] == 0:
            print(str(collection_number) + '/' + str(collection_amount))
        collection_number += 1
    
        for document in collection_documents:
            search_collection = document_database.replace('|','-') + '-' + collection_prefix
            document_identity = document_database + '-' + document_collection + '-' + str(document['_id'])

            if document_identity in document_identities:
                continue
        
            document_keywords = create_document_keywords(
                actor_ref = actor_ref,
                database = document_database,
                collection = document_collection,
                document = document,
                index = document_index
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
