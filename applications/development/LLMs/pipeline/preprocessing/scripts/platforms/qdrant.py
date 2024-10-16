from qdrant_client import QdrantClient as qc

def qdrant_is_client(
    storage_client: any
) -> any:
    try:
        return isinstance(storage_client, qc.Connection)
    except Exception as e:
        return False

def qdrant_setup_client(
    api_key: str,
    address: str, 
    port: str
) -> any:
    try:
        qdrant_client = qc(
            host = address,
            port = int(port),
            api_key = api_key,
            https = False
        ) 
        return qdrant_client
    except Exception as e:
        return None

def qdrant_create_collection(
    qdrant_client: any, 
    collection_name: str,
    configuration: any
) -> any:
    try:
        result = qdrant_client.create_collection(
            collection_name = collection_name,
            vectors_config = configuration
        )
        return result
    except Exception as e:
        return None

def qdrant_get_collections(
    qdrant_client: any, 
    collection_name: str
) -> any:
    try:
        collection = qdrant_client.get_collection(
            collection_name = collection_name
        )
        return collection
    except Exception as e:
        return None

def qdrant_list_collections(
    qdrant_client: any, 
    database_name: str
) -> any:
    try:
        collections = qdrant_client.get_collections()
        return collections
    except Exception as e:
        return []

def qdrant_remove_collection(
    qdrant_client: any, 
    collection_name: str
) -> bool:
    try:
        qdrant_client.delete_collection(collection_name)
        return True
    except Exception as e:
        return False

def qdrant_upsert_points(
    qdrant_client: qc, 
    collection_name: str,
    points: any
) -> any:
    try:
        results = qdrant_client.upsert(
            collection_name = collection_name, 
            points = points
        )
        return results
    except Exception as e:
        return None

def qdrant_search_vectors(
    qdrant_client: qc,  
    collection_name: str,
    query_vector: any,
    limit: str
) -> any:
    try:
        hits = qdrant_client.search(
            collection_name = collection_name,
            query_vector = query_vector,
            limit = limit
        )
        return hits
    except Exception as e:
        return []

def qdrant_remove_vectors(
    qdrant_client: qc,  
    collection_name: str, 
    vectors: str
) -> bool:
    try:
        results = qdrant_client.delete_vectors(
            collection_name = collection_name,
            vectors = vectors
        )
        return results
    except Exception as e:
        print(f"Error removing document: {e}")
        return None
