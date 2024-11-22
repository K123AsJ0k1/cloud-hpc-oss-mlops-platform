from platforms.mongodb import *
from bson.objectid import ObjectId

from prompts import *
from search import *
from ranking import *

def create_context(
    mongo_client: any,
    documents: any
) -> any:
    context = ''
    for metadata in documents:
        database = metadata[1]
        collection = metadata[2]
        document = metadata[3]
        data = mongo_get_document(
            mongo_client = mongo_client, 
            database_name = database, 
            collection_name = collection, 
            filter_query = {
                '_id': ObjectId(document)
            }
        )
        context += data['data']
    return context

def context_pipeline(
    document_client: any,
    vector_client: any,
    search_client: any,
    configuration: any,
    prompt: any
) -> any:
    prompt_query = generate_prompt_queries(
        configuration = configuration,
        prompt = prompt
    )

    prompt_hits = get_vector_search_hits(
        vector_client = vector_client,
        search_client = search_client,
        configuration = configuration,
        queries = prompt_query
    )

    prompt_documents = get_top_documents(
        hits = prompt_hits,
        configuration = configuration
    ) 

    prompt_context = create_context(
        mongo_client = document_client,
        documents = prompt_documents
    )

    return prompt_context