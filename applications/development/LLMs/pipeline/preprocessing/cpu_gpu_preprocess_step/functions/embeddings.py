
import ray

import re
import hashlib

from qdrant_client.models import VectorParams, Distance, PointStruct

from langchain_text_splitters import Language

from functions.utility import generate_uuid
from functions.documents import get_sorted_documents
from functions.mongo_db import mongo_setup_client
from functions.langchain import langchain_create_code_chunks, langchain_create_text_chunks
from functions.qdrant_vb import qdrant_setup_client, qdrant_list_collections, qdrant_create_collection, qdrant_upsert_points

def generate_hash(
    chunk: any
) -> any:
    chunk = re.sub(r'[^\w\s]', '', chunk)
    chunk = re.sub(r'\s+', ' ', chunk) 
    chunk = chunk.strip()
    chunk = chunk.lower()
    return hashlib.md5(chunk.encode('utf-8')).hexdigest()

def create_document_embeddings(
    actor_ref: any,
    vector_client: any,
    data_parameters: any,
    vector_collection: str,
    database: str,
    collection: str,
    document: any,
    index: int
) -> bool:
    id = str(document['_id'])
    type = document['type']
    data = document['data']

    chunks = []
    embeddings = []
    try:
        created_chunks = []
        if type == 'python':
            used_configuration = data_parameters[type]
            created_chunks = langchain_create_code_chunks(
                language = Language.PYTHON,
                chunk_size = used_configuration['chunk-size'],
                chunk_overlap = used_configuration['chunk-overlap'],
                code = data
            )
        if type == 'text' or type == 'yaml' or type == 'markdown':
            used_configuration = data_parameters[type]
            created_chunks = langchain_create_text_chunks(
                chunk_size = used_configuration['chunk-size'],
                chunk_overlap = used_configuration['chunk-overlap'],
                text = data
            )
            
        for chunk in created_chunks:
            if chunk.strip() and 2 < len(chunk):
                chunks.append(chunk)
            
        embeddings = ray.get(actor_ref.create_embeddings.remote(
            chunks = chunks
        ))
    except Exception as e:
        print(database,collection,id)
        print(e)

    if 0 == len(chunks) or 0 == len(embeddings):
        return [None, None]
    
    vector_collections = qdrant_list_collections(
        qdrant_client = vector_client
    )
    
    if not vector_collection in vector_collections:
        try:
            collection_configuration = VectorParams(
                size = len(embeddings[0]), 
                distance = Distance.COSINE
            )
            collection_created = qdrant_create_collection(
                qdrant_client = vector_client,
                collection_name = vector_collection,
                configuration = collection_configuration
            )
        except Exception as e:
            print(e)

    embedding_index = index
    chunk_index = 0
    added_hashes = []
    vector_points = []
    for chunk in chunks:
        embedding_uuid = generate_uuid(
            id = id,
            index = embedding_index
        )

        chunk_hash = generate_hash(
            chunk = chunk
        )
        
        if not chunk_hash in added_hashes:
            given_vector = embeddings[chunk_index]

            chunk_point = PointStruct(
                id = embedding_uuid, 
                vector = given_vector,
                payload = {
                    'database': database,
                    'collection': collection,
                    'document': id,
                    'type': type,
                    'chunk': chunk,
                    'chunk_hash': chunk_hash
                }
            )
            added_hashes.append(chunk_hash)
            vector_points.append(chunk_point)
        chunk_index += 1
        embedding_index += 1
    return [embedding_index, vector_points]

@ray.remote(
    num_cpus = 1,
    memory = 4 * 1024 * 1024 * 1024
)
def store_embeddings(
    actor_ref: any,
    storage_parameters: any,
    data_parameters: any,
    collection_tuples: any,
    given_identities: any
):
    collection_amount = len(collection_tuples)
    print('Storing embeddings of ' + str(collection_amount) + ' collections')
    
    document_client = mongo_setup_client(
        username = storage_parameters['mongo-username'], 
        password = storage_parameters['mongo-password'],
        address = storage_parameters['mongo-address'],
        port = storage_parameters['mongo-port']
    )

    vector_client = qdrant_setup_client(
        api_key = storage_parameters['qdrant-key'],
        address = storage_parameters['qdrant-address'], 
        port = storage_parameters['qdrant-port']
    )
    
    collection_prefix = storage_parameters['vector-collection-prefix']
    document_identities = given_identities
    embedding_index = len(document_identities)
    collection_number = 1
    for collection_tuple in collection_tuples:
        document_database = collection_tuple[0]
        document_collection = collection_tuple[1]
        
        collection_documents = get_sorted_documents(
            document_client = document_client,
            database = document_database,
            collection = document_collection
        )

        if collection_number % data_parameters['vector-collection-print'] == 0:
            print(str(collection_number) + '/' + str(collection_amount))
        collection_number += 1

        for document in collection_documents:
            vector_collection = document_database.replace('|','-') + '-' + collection_prefix
            document_identity = document_database + '-' + document_collection + '-' + str(document['_id'])

            if document_identity in document_identities:
                continue
                
            output = create_document_embeddings(
                actor_ref = actor_ref,
                vector_client = vector_client,
                data_parameters = data_parameters,
                vector_collection = vector_collection,
                database = document_database,
                collection = document_collection,
                document = document,
                index = embedding_index
            )

            if not output[0] is None:
                if 0 < len(output[-1]):
                    # Maybe upsert points in batches to remove timeouts
                    points_stored = qdrant_upsert_points( 
                        qdrant_client = vector_client, 
                        collection_name = vector_collection,
                        points = output[-1]
                    )
                    embedding_index = output[0]
                    document_identities.append(document_identity)
    return document_identities
