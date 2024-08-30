import meilisearch as ms
from meilisearch.errors import MeiliSearchError

def meili_is_client(
    storage_client: any
) -> any:
    try:
        return isinstance(storage_client, ms.Connection)
    except Exception as e:
        return False

def meili_setup_client(
    host: str, 
    master_key: str
) -> any:
    try:
        meili_client = ms.Client(
            host = host, 
            master_key = master_key
        )
        return meili_client 
    except Exception as e:
        return None

def meili_create_index(
    meili_client: any, 
    index_name: str
) -> any:
    try:
        response = meili_client.create_index(
            uid = index_name
        )
        return response
    except Exception as e:
        return None

def meili_add_documents(
    meili_client: any, 
    index_name: str, 
    documents: any
) -> any:
    try:
        index = meili_client.index(
            index_name = index_name
        )
        response = index.add_documents(
            documents = documents
        )
        return response
    except Exception as e:
        return None

def meili_search_documents(
    meili_client: any, 
    index_name: str, 
    query: any, 
    options: any
) -> any:
    try:
        index = meili_client.index(
            index_name = index_name
        )
        response = index.search(
            query = query, 
            options = options
        )
        return response
    except Exception as e:
        return None
    
def meili_update_documents(
    meili_client, 
    index_name, 
    documents
) -> any:
    try:
        index = meili_client.index(
            index_name = index_name
        )
        response = index.update_documents(
            documents = documents
        )
        return response
    except Exception as e:
        return None

def meili_delete_documents(
    meili_client: any, 
    index_name: str, 
    ids: any
) -> any:
    try:
        index = meili_client.index(
            index_name = index_name
        )
        response = index.delete_documents(
            document_ids = ids
        )
        return response
    except Exception as e:
        return None