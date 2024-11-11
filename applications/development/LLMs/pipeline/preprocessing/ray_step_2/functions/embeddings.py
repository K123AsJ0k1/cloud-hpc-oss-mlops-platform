
import ray

import re
import uuid

import hashlib

from qdrant_client import models
from qdrant_client.models import VectorParams, Distance, PointStruct

from langchain_text_splitters import (
    Language
)

from functions.langchain import langchain_create_code_chunks, langchain_create_text_chunks, langchain_create_chunk_embeddings
from functions.qdrant_vb import qdrant_setup_client, qdrant_search_data, qdrant_list_collections, qdrant_create_collection, qdrant_upsert_points

def create_packet(
    document: any,
    configuration: any,
) -> any:
    document_type = document['type']
    used_configuration = configuration[document_type]
    
    document_chunks = []
    if document_type == 'python':
        document_chunks = langchain_create_code_chunks(
            language = Language.PYTHON,
            chunk_size = used_configuration['chunk-size'],
            chunk_overlap = used_configuration['chunk-overlap'],
            code = document['data']
        )
    if document_type == 'text' or document_type == 'yaml' or document_type == 'markdown':
        document_chunks = langchain_create_text_chunks(
            chunk_size = used_configuration['chunk-size'],
            chunk_overlap = used_configuration['chunk-overlap'],
            text = document['data']
        )
    
    filtered_chunks = []
    for chunk in document_chunks:
        if chunk.strip() and 2 < len(chunk):
            filtered_chunks.append(chunk)
        
    vector_embedding = langchain_create_chunk_embeddings(
        model_name = used_configuration['model-name'],
        chunks = filtered_chunks
    )

    packet = {
        'chunks': filtered_chunks,
        'embeddings': vector_embedding
    }
    
    return packet

def format_chunk(
    chunk: any
) -> any:
    chunk = re.sub(r'[^\w\s]', '', chunk)
    chunk = re.sub(r'\s+', ' ', chunk) 
    chunk = chunk.strip()
    chunk = chunk.lower()
    # This helps to remove unique hashes for duplicates such as:
    # task_id = task_id )
    # task_id = task_id 
    # task_id = task_id )
    return chunk

def generate_hash(
    chunk: any
) -> any:
    cleaned_chunk = format_chunk(
        chunk = chunk
    )
    return hashlib.md5(cleaned_chunk.encode('utf-8')).hexdigest()

def generate_document_embeddings(
    vector_client: any,
    document_database: any,
    document_collection: any,
    document_type: any,
    document_id: str, 
    document_chunks: any,
    document_embeddings: any,
    vector_collection: any
):
    vector_points = []
    vector_index = 0
    added_hashes = []
    for chunk in document_chunks:
        vector_id = document_id + '-' + str(vector_index + 1)
        vector_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, vector_id))

        chunk_hash = generate_hash(
            chunk = chunk
        )
        
        existing_chunks = qdrant_search_data(
            qdrant_client = vector_client,
            collection_name = vector_collection,
            scroll_filter = models.Filter(
                must = [
                    models.FieldCondition(
                        key = 'chunk_hash',
                        match = models.MatchValue(
                            value = chunk_hash
                        )
                    )
                ]
            ),
            limit = 1
        )

        # Removes duplicates
        if not len(existing_chunks) == 0:
            if len(existing_chunks[0]) == 0:
                if not chunk_hash in added_hashes:
                    given_vector = document_embeddings[vector_index]

                    chunk_point = PointStruct(
                        id = vector_uuid, 
                        vector = given_vector,
                        payload = {
                            'database': document_database,
                            'collection': document_collection,
                            'document': document_id,
                            'type': document_type,
                            'chunk': chunk,
                            'chunk_hash': chunk_hash
                        }
                    )
                    added_hashes.append(chunk_hash)
                    vector_points.append(chunk_point)
        vector_index += 1
    return vector_points

def create_document_embeddings(
    vector_client: any,
    document_database,
    document_collection,
    document: any,
    configuration: any,
    vector_collection: str
) -> bool:
    document_id = str(document['_id'])
    document_type = document['type']

    document_packet = {}
    try:
        document_packet = create_packet(
            document = document,
            configuration = configuration
        )
    except Exception as e:
        print(document_database,document_collection,document_id)
        print(e)

    if 0 == len(document_packet):
        return []
        
    document_chunks = document_packet['chunks']
    document_embeddings = document_packet['embeddings']
    
    if 0 == len(document_embeddings):
        return []
    
    vector_collections = qdrant_list_collections(
        qdrant_client = vector_client
    )
    
    collection_created = None
    if not vector_collection in vector_collections:
        collection_configuration = VectorParams(
            size = len(document_embeddings[0]), 
            distance = Distance.COSINE
        )
        collection_created = qdrant_create_collection(
            qdrant_client = vector_client,
            collection_name = vector_collection,
            configuration = collection_configuration
        )

    vector_points = generate_document_embeddings(
        vector_client = vector_client,
        document_database = document_database,
        document_collection = document_collection,
        document_type = document_type,
        document_id = document_id,
        document_chunks = document_chunks,
        document_embeddings = document_embeddings,
        vector_collection = vector_collection
    )

    return vector_points

@ray.remote(
    num_cpus = 1,
    memory = 9 * 1024 * 1024 * 1024
)
def store_embeddings(
    storage_parameters: any,
    configuration: any,
    storage_documents: any,
    given_identities: any
):
    vector_client = qdrant_setup_client(
        api_key = storage_parameters['qdrant-key'],
        address = storage_parameters['qdrant-address'], 
        port = storage_parameters['qdrant-port']
    )
    
    collection_prefix = configuration['vector-prefix']
    document_identities = given_identities
    for document_tuple in storage_documents:
        document_database = document_tuple[0]
        document_collection = document_tuple[1]
        document = document_tuple[2]
        vector_collection = document_database.replace('|','-') + '-' + collection_prefix
        
        document_identity = document_database + '-' + document_collection + '-' + str(document['_id'])

        if document_identity in document_identities:
            continue
            
        document_vectors = create_document_embeddings(
            vector_client = vector_client,
            document_database = document_database,
            document_collection = document_collection,
            document = document,
            configuration = configuration,
            vector_collection = vector_collection
        )

        if 0 < len(document_vectors):
            points_stored = qdrant_upsert_points(
                qdrant_client = vector_client, 
                collection_name = vector_collection,
                points = document_vectors
            )
            
            document_identities.append(document_identity)
    return document_identities
