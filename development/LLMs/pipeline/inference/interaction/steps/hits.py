
from platforms.qdrant_vb import qdrant_list_collections, qdrant_search_vectors
from platforms.meili_sb import meili_list_indexes, meili_search_documents

def calculate_keyword_score(
    keyword_query: str,
    keyword_list: any
) -> any:
    match = 0
    asked_keywords = keyword_query.split('OR')
    for asked_keyword in asked_keywords:
        formatted = asked_keyword.replace('keywords =', '')
        formatted = formatted.replace('"', '')
        formatted = formatted.replace(' ', '')
        
        if formatted in keyword_list:
            match += 1
            
    query_length = len(asked_keywords)
    keyword_length = len(keyword_list)

    if match == 0:
        return 0.0

    normalized = match / ((query_length * keyword_length) ** 0.5)
    return normalized

def get_vector_hits(
    vector_client: any,
    configuration: any,
    embedding_queries: any
) -> any:
    recommeded_cases = []

    collections = qdrant_list_collections(
        qdrant_client = vector_client
    )
    for collection in collections:
        for embedding in embedding_queries:
            results = qdrant_search_vectors(
                qdrant_client = vector_client,  
                collection_name = collection,
                query_vector = embedding,
                limit = configuration['top-k']
            ) 
            
            for result in results:
                res_database = result.payload['database']
                res_collection = result.payload['collection']
                res_document = result.payload['document']
                res_type = result.payload['type']
                res_score = result.score
                
                res_case = {
                    'source': 'vector',
                    'database': res_database,
                    'collection': res_collection,
                    'document': res_document,
                    'type': res_type,
                    'score': res_score
                }
                
                recommeded_cases.append(res_case)
    return recommeded_cases

def get_search_hits(
    search_client: any,
    configuration: any,
    keyword_queries: any
) -> any:
    recommeded_cases = []
    collections = meili_list_indexes(
        meili_client = search_client
    )
    
    for collection in collections:        
        for keywords in keyword_queries:
            results = meili_search_documents(
                meili_client = search_client, 
                index_name = collection, 
                query = "", 
                options = {
                    'filter': keywords,
                    'attributesToRetrieve': ['database','collection','document', 'type', 'keywords'],
                    'limit': configuration['top-k']
                }
            )
    
            for result in results['hits']:
                res_database = result['database']
                res_collection = result['collection']
                res_document = result['document']
                res_type = result['type']
                res_keywords = result['keywords']
                
                
                res_score = calculate_keyword_score(
                    keyword_query = keywords,
                    keyword_list = res_keywords
                )
    
                res_case = {
                    'source': 'search',
                    'database': res_database,
                    'collection': res_collection,
                    'document': res_document,
                    'type': res_type,
                    'score': res_score
                }
    
                recommeded_cases.append(res_case)
    return recommeded_cases
    
def get_vector_search_hits(
    vector_client: any,
    search_client: any,
    configuration: any,
    queries: any
) -> any:
    vector_hits = get_vector_hits(
        vector_client = vector_client,
        configuration = configuration,
        embedding_queries = queries['embeddings']
    )
    
    search_hits = get_search_hits(
        search_client = search_client,
        configuration = configuration,
        keyword_queries = queries['keywords']
    )

    found_hits = vector_hits + search_hits

    return found_hits