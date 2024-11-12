
import ray

import re
import uuid

import hashlib

from qdrant_client.models import VectorParams, Distance, PointStruct

from langchain_text_splitters import (
    Language
)

from functions.documents import get_sorted_documents
from functions.mongo_db import mongo_setup_client

from functions.langchain import langchain_create_code_chunks, langchain_create_text_chunks, langchain_create_chunk_embeddings
from functions.qdrant_vb import qdrant_setup_client, qdrant_search_data, qdrant_list_collections, qdrant_create_collection, qdrant_upsert_points

def create_packet(
    document: any,
    data_parameters: any,
) -> any:
    document_data = document['data']
    document_type = document['type']
    used_configuration = data_parameters[document_type]
    
    document_chunks = []
    if document_type == 'python':
        document_chunks = langchain_create_code_chunks(
            language = Language.PYTHON,
            chunk_size = used_configuration['chunk-size'],
            chunk_overlap = used_configuration['chunk-overlap'],
            code = document_data
        )
    if document_type == 'text' or document_type == 'yaml' or document_type == 'markdown':
        document_chunks = langchain_create_text_chunks(
            chunk_size = used_configuration['chunk-size'],
            chunk_overlap = used_configuration['chunk-overlap'],
            text = document_data
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
    return chunk

def generate_hash(
    chunk: any
) -> any:
    cleaned_chunk = format_chunk(
        chunk = chunk
    )
    return hashlib.md5(cleaned_chunk.encode('utf-8')).hexdigest()

def generate_document_embeddings(
    database: any,
    collection: any,
    type: any,
    id: str, 
    chunks: any,
    embeddings: any
):
    vector_index = 0
    added_hashes = []
    vector_points = []
    for chunk in chunks:
        vector_id = id + '-' + str(vector_index + 1)
        vector_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, vector_id))

        chunk_hash = generate_hash(
            chunk = chunk
        )
        
        if not chunk_hash in added_hashes:
            given_vector = embeddings[vector_index]

            chunk_point = PointStruct(
                id = vector_uuid, 
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
        vector_index += 1
    return vector_points

def create_document_embeddings(
    vector_client: any,
    document_database,
    document_collection,
    document: any,
    data_parameters: any,
    vector_collection: str
) -> bool:
    document_id = str(document['_id'])
    document_type = document['type']

    document_packet = {}
    try:
        document_packet = create_packet(
            document = document,
            data_parameters = data_parameters
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
    
    if not vector_collection in vector_collections:
        try:
            collection_configuration = VectorParams(
                size = len(document_embeddings[0]), 
                distance = Distance.COSINE
            )
            collection_created = qdrant_create_collection(
                qdrant_client = vector_client,
                collection_name = vector_collection,
                configuration = collection_configuration
            )
        except Exception as e:
            print(e)

    return generate_document_embeddings(
        database = document_database,
        collection = document_collection,
        type = document_type,
        id = document_id,
        chunks = document_chunks,
        embeddings = document_embeddings
    )

@ray.remote(
    num_cpus = 1,
    memory = 4 * 1024 * 1024 * 1024
)
def store_embeddings(
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
    print('Storing embeddings of ' + str(all_collections) + ' collections')
    vector_client = qdrant_setup_client(
        api_key = storage_parameters['qdrant-key'],
        address = storage_parameters['qdrant-address'], 
        port = storage_parameters['qdrant-port']
    )
    
    collection_prefix = storage_parameters['vector-collection-prefix']
    document_identities = given_identities
    #all_collection_amount = len(collection_tuples)
    collection_index = 0
    for collection_tuple in collection_tuples:
        document_database = collection_tuple[0]
        document_collection = collection_tuple[1]
        
        collection_documents = get_sorted_documents(
            document_client = document_client,
            database = document_database,
            collection = document_collection
        )

        if collection_index % data_parameters['vector-collection-print'] == 0:
            print(str(collection_index) + '/' + str(all_collections))
        collection_index += 1

        for document in collection_documents:
            vector_collection = document_database.replace('|','-') + '-' + collection_prefix
            document_identity = document_database + '-' + document_collection + '-' + str(document['_id'])

            if document_identity in document_identities:
                continue
                
            document_embeddings = create_document_embeddings(
                vector_client = vector_client,
                document_database = document_database,
                document_collection = document_collection,
                document = document,
                data_parameters = data_parameters,
                vector_collection = vector_collection
            )

            if 0 < len(document_embeddings):
                points_stored = qdrant_upsert_points( 
                    qdrant_client = vector_client, 
                    collection_name = vector_collection,
                    points = document_embeddings
                )
                document_identities.append(document_identity)
    return document_identities
