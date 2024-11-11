
import ray

import uuid

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
    document_database: str,
    document_collection: str,
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

    payload = {
        'id': keyword_uuid,
        'database': document_database,
        'collection': document_collection,
        'document': document_id,
        'type': document_type,
        'keywords': document_keywords
    }

    return payload

@ray.remote(
    num_cpus = 1,
    memory = 9 * 1024 * 1024 * 1024
)
def store_keywords(
    storage_parameters: any,
    configuration: any,
    storage_documents: any,
    given_identities: any
):
    search_client = meili_setup_client(
        api_key = storage_parameters['meili-key'],
        host = storage_parameters['meili-host']
    )
    
    collection_prefix = configuration['search-prefix']
    document_identities = given_identities
    document_index = 1
    for document_tuple in storage_documents:
        document_database = document_tuple[0]
        document_collection = document_tuple[1]
        document = document_tuple[2]
        
        search_collection = document_database.replace('|','-') + '-' + collection_prefix
        document_identity = document_database + '-' + document_collection + '-' + str(document['_id'])
    
        if document_identity in document_identities:
            continue
    
        document_keywords = create_document_keywords(
            document_database = document_database,
            document_collection = document_collection,
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
