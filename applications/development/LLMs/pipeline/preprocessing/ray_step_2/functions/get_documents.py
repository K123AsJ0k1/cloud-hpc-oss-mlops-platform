
from pymongo import ASCENDING

from functions.mongo_db import mongo_list_databases, mongo_list_collections, mongo_list_documents

def get_stored_documents(
    document_client: any,
    database_prefix: str
) -> any:
    storage_structure = {}
    database_list = mongo_list_databases(
        mongo_client = document_client
    )
    for database_name in database_list:
        if database_prefix in database_name:
            collection_list = mongo_list_collections(
                mongo_client = document_client,
                database_name = database_name
            )
            storage_structure[database_name] = collection_list
    
    storage_documents = []
    for database_name, collections in storage_structure.items():
        for collection_name in collections:
            collection_documents = mongo_list_documents(
                mongo_client = document_client,
                database_name = database_name,
                collection_name = collection_name,
                filter_query = {},
                sorting_query = [
                    ('index', ASCENDING),
                    ('sub-index', ASCENDING)
                ]
            )
            for document in collection_documents:
                document_tuple = (database_name, collection_name, document)
                storage_documents.append(document_tuple)
    return storage_documents
