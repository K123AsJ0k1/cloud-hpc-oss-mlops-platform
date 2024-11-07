import sys
import ray
import json

from pymongo import MongoClient as mc

import re

from pymongo import ASCENDING

from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
)
from langchain_huggingface import HuggingFaceEmbeddings
import hashlib
import uuid
import re
from qdrant_client import QdrantClient as qc
from qdrant_client import models
from qdrant_client.models import VectorParams, Distance
from qdrant_client.models import PointStruct
import spacy

import io
import pickle
from minio import Minio
import meilisearch as ms

def get_github_storage_prefix(
    repository_owner: str,
    repository_name: str
) -> str:
    return repository_owner + '|' + repository_name + '|'

def mongo_is_client(
    storage_client: any
) -> any:
    return isinstance(storage_client, mc.Connection)

def mongo_setup_client(
    username: str,
    password: str,
    address: str,
    port: str
) -> any:
    connection_prefix = 'mongodb://(username):(password)@(address):(port)/'
    connection_address = connection_prefix.replace('(username)', username)
    connection_address = connection_address.replace('(password)', password)
    connection_address = connection_address.replace('(address)', address)
    connection_address = connection_address.replace('(port)', port)
    mongo_client = mc(
        host = connection_address
    )
    return mongo_client

def mongo_get_database(
    mongo_client: any,
    database_name: str
) -> any:
    try:
        database = mongo_client[database_name]
        return database
    except Exception as e:
        return None

def mongo_check_database(
    mongo_client: any, 
    database_name: str
) -> bool:
    try:
        database_exists = database_name in mongo_client.list_database_names()
        return database_exists
    except Exception as e:
        return False

def mongo_list_databases(
    mongo_client: any
) -> any:
    try:
        databases = mongo_client.list_database_names()
        return databases
    except Exception as e:
        return []

def mongo_remove_database(
    mongo_client: any, 
    database_name: str
) -> bool:
    try:
        mongo_client.drop_database(database_name)
        return True
    except Exception as e:
        return False

def mongo_get_collection(
    mongo_client: any, 
    database_name: str, 
    collection_name: str
) -> bool:
    try:
        database = mongo_get_database(
            mongo_client = mongo_client,
            database_name = database_name
        )
        collection = database[collection_name]
        return collection
    except Exception as e:
        return None
    
def mongo_check_collection(
    mongo_client: any, 
    database_name: any, 
    collection_name: any
) -> bool:
    try:
        database = mongo_client[database_name]
        collection_exists = collection_name in database.list_collection_names()
        return collection_exists
    except Exception as e:
        return False

def mongo_update_collection(
    mongo_client: any, 
    database_name: str, 
    collection_name: str, 
    filter_query: any, 
    update_query: any
) -> any:
    try:
        collection = mongo_get_collection(
            mongo_client = mongo_client, 
            database_name = database_name, 
            collection_name = collection_name
        )
        result = collection.update_many(filter_query, update_query)
        return result
    except Exception as e:
        return None

def mongo_list_collections(
    mongo_client: any, 
    database_name: str
) -> bool:
    try:
        database = mongo_get_database(
            mongo_client = mongo_client,
            database_name = database_name
        )
        collections = database.list_collection_names()
        return collections
    except Exception as e:
        return []

def mongo_remove_collection(
    mongo_client: any, 
    database_name: str, 
    collection_name: str
) -> bool:
    try: 
        database = mongo_get_database(
            mongo_client = mongo_client,
            database_name = database_name
        )
        database.drop_collection(collection_name)
        return True
    except Exception as e:
        return False

def mongo_create_document(
    mongo_client: any, 
    database_name: str, 
    collection_name: str, 
    document: any
) -> any:
    try: 
        collection = mongo_get_collection(
            mongo_client = mongo_client, 
            database_name = database_name, 
            collection_name = collection_name
        )
        result = collection.insert_one(document)
        return result
    except Exception as e:
        return None

def mongo_get_document(
    mongo_client: any, 
    database_name: str, 
    collection_name: str, 
    filter_query: any
):
    try: 
        collection = mongo_get_collection(
            mongo_client = mongo_client, 
            database_name = database_name, 
            collection_name = collection_name
        )
        document = collection.find_one(filter_query)
        return document
    except Exception as e:
        print(e)
        return None 

def mongo_list_documents(
    mongo_client: any, 
    database_name: str, 
    collection_name: str, 
    filter_query: any,
    sorting_query: any
) -> any:
    try: 
        collection = mongo_get_collection(
            mongo_client = mongo_client, 
            database_name = database_name, 
            collection_name = collection_name
        )
        documents = list(collection.find(filter_query).sort(sorting_query))
        return documents
    except Exception as e:
        return []

def mongo_update_document(
    mongo_client: any, 
    database_name: any, 
    collection_name: any, 
    filter_query: any, 
    update_query: any
) -> any:
    try: 
        collection = mongo_get_collection(
            mongo_client = mongo_client, 
            database_name = database_name, 
            collection_name = collection_name
        )
        result = collection.update_one(filter_query, update_query)
        return result
    except Exception as e:
        return None

def mongo_remove_document(
    mongo_client: any, 
    database_name: str, 
    collection_name: str, 
    filter_query: any
) -> bool:
    try: 
        collection = mongo_get_collection(
            mongo_client = mongo_client, 
            database_name = database_name, 
            collection_name = collection_name
        )
        result = collection.delete_one(filter_query)
        return result
    except Exception as e:
        return None
    
def get_stored_documents(
    mongo_client: any,
    database_prefix: str
) -> any:
    storage_structure = {}
    database_list = mongo_list_databases(
        mongo_client = mongo_client
    )
    for database_name in database_list:
        if database_prefix in database_name:
            collection_list = mongo_list_collections(
                mongo_client = mongo_client,
                database_name = database_name
            )
            storage_structure[database_name] = collection_list
    
    storage_documents = {}
    for database_name, collections in storage_structure.items():
        if not database_name in storage_documents:
            storage_documents[database_name] = {}
        for collection_name in collections:
            collection_documents = mongo_list_documents(
                mongo_client = mongo_client,
                database_name = database_name,
                collection_name = collection_name,
                filter_query = {},
                sorting_query = [
                    ('index', ASCENDING),
                    ('sub-index', ASCENDING)
                ]
            )
            storage_documents[database_name][collection_name] = collection_documents
            
    return storage_documents

def is_minio_client(
    storage_client: any
) -> bool:
    return isinstance(storage_client, Minio)

def setup_minio(
    endpoint: str,
    username: str,
    password: str
) -> any:
    minio_client = Minio(
        endpoint = endpoint, 
        access_key = username, 
        secret_key = password,
        secure = False
    )
    return minio_client

def pickle_data(
    data: any
) -> any:
    pickled_data = pickle.dumps(data)
    length = len(pickled_data)
    buffer = io.BytesIO()
    buffer.write(pickled_data)
    buffer.seek(0)
    return buffer, length

def unpickle_data(
    pickled: any
) -> any:
    return pickle.loads(pickled)

def minio_create_bucket(
    minio_client: any,
    bucket_name: str
) -> bool: 
    try:
        minio_client.make_bucket(
            bucket_name = bucket_name
        )
        return True
    except Exception as e:
        print('MinIO bucket creation error')
        print(e)
        return False
    
def minio_check_bucket(
    minio_client: any,
    bucket_name:str
) -> bool:
    try:
        status = minio_client.bucket_exists(
            bucket_name = bucket_name
        )
        return status
    except Exception as e:
        print('MinIO bucket checking error')
        print(e)
        return False 
       
def minio_delete_bucket(
    minio_client: any,
    bucket_name:str
) -> bool:
    try:
        minio_client.remove_bucket(
            bucket_name = bucket_name
        )
        return True
    except Exception as e:
        print('MinIO bucket deletion error')
        print(e)
        return False
# Works
def minio_create_object(
    minio_client: any,
    bucket_name: str, 
    object_path: str, 
    data: any,
    metadata: dict
) -> bool: 
    # Be aware that MinIO objects have a size limit of 1GB, 
    # which might result to large header error    
    
    try:
        buffer, length = pickle_data(
            data = data
        )

        minio_client.put_object(
            bucket_name = bucket_name,
            object_name = object_path,
            data = buffer,
            length = length,
            metadata = metadata
        )
        return True
    except Exception as e:
        print('MinIO object creation error')
        print(e)
        return False
# Works
def minio_check_object(
    minio_client: any,
    bucket_name: str, 
    object_path: str
) -> any: 
    try:
        object_info = minio_client.stat_object(
            bucket_name = bucket_name,
            object_name = object_path
        )      
        return object_info
    except Exception as e:
        return {}
# Works
def minio_delete_object(
    minio_client: any,
    bucket_name: str, 
    object_path: str
) -> bool: 
    try:
        minio_client.remove_object(
            bucket_name = bucket_name, 
            object_name = object_path
        )
        return True
    except Exception as e:
        print('MinIO object deletion error')
        print(e)
        return False
# Works
def minio_update_object(
    minio_client: any,
    bucket_name: str, 
    object_path: str, 
    data: any,
    metadata: dict
) -> bool:  
    remove = minio_delete_object(
        minio_client = minio_client,
        bucket_name = bucket_name,
        object_path = object_path
    )
    if remove:
        return minio_create_object(
            minio_client = minio_client, 
            bucket_name = bucket_name, 
            object_path = object_path, 
            data = data,
            metadata = metadata
        )
    return False
# works
def minio_create_or_update_object(
    minio_client: any,
    bucket_name: str, 
    object_path: str, 
    data: any, 
    metadata: dict
) -> bool:
    bucket_status = minio_check_bucket(
        minio_client = minio_client,
        bucket_name = bucket_name
    )
    if not bucket_status:
        creation_status = minio_create_bucket(
            minio_client = minio_client,
            bucket_name = bucket_name
        )
        if not creation_status:
            return False
    object_status = minio_check_object(
        minio_client = minio_client,
        bucket_name = bucket_name, 
        object_path = object_path
    )
    if not object_status:
        return minio_create_object(
            minio_client = minio_client,
            bucket_name = bucket_name, 
            object_path = object_path, 
            data = data, 
            metadata = metadata
        )
    else:
        return minio_update_object(
            minio_client = minio_client,
            bucket_name = bucket_name, 
            object_path = object_path, 
            data = data, 
            metadata = metadata
        )
# Works
def minio_get_object_list(
    minio_client: any,
    bucket_name: str,
    path_prefix: str
) -> any:
    try:
        objects = minio_client.list_objects(
            bucket_name = bucket_name, 
            prefix = path_prefix, 
            recursive = True
        )
        return objects
    except Exception as e:
        return None  
    
def minio_get_object_data_and_metadata(
    minio_client: any,
    bucket_name: str, 
    object_path: str
) -> any:
    try:
        given_object_data = minio_client.get_object(
            bucket_name = bucket_name, 
            object_name = object_path
        )
        
        # There seems to be some kind of a limit
        # with the amount of request a client 
        # can make, which is why this variable
        # is set here to give more time got the client
        # to complete the request

        given_data = unpickle_data(
            pickled = given_object_data.data
        )
        
        given_object_info = minio_client.stat_object(
            bucket_name = bucket_name, 
            object_name = object_path
        )
        
        given_metadata = given_object_info.metadata
        
        return {'data': given_data, 'metadata': given_metadata}
    except Exception as e:
        print('MinIO object fetching error')
        print(e)
        return None

def langchain_create_code_chunks(
    language: any,
    chunk_size: int,
    chunk_overlap: int,
    document: any
) -> any:
    splitter = RecursiveCharacterTextSplitter.from_language(
        language = language,
        chunk_size = chunk_size, 
        chunk_overlap = chunk_overlap
    )

    code_chunks = splitter.create_documents([document])
    code_chunks = [doc.page_content for doc in code_chunks]
    return code_chunks

def langchain_create_text_chunks(
    chunk_size: int,
    chunk_overlap: int,
    document: any
) -> any:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size = chunk_size, 
        chunk_overlap = chunk_overlap,
        length_function = len,
        is_separator_regex = False
    )

    text_chunks = splitter.create_documents([document])
    text_chunks = [doc.page_content for doc in text_chunks]
    return text_chunks

def langchain_create_chunk_embeddings(
    model_name: str,
    chunks: any
) -> any:
    embedding_model = HuggingFaceEmbeddings(
        model_name = model_name
    )
    chunk_embeddings = embedding_model.embed_documents(
        texts = chunks
    )
    return chunk_embeddings

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
        print(e)
        return None

def qdrant_get_collection(
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
    qdrant_client: any
) -> any:
    try:
        collections = qdrant_client.get_collections()
        collection_list = []
        for description in collections.collections:
            collection_list.append(description.name)
        return collection_list
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
        print(e)
        return None

def qdrant_search_data(
    qdrant_client: qc,  
    collection_name: str,
    scroll_filter: any,
    limit: str
) -> any:
    try:
        hits = qdrant_client.scroll(
            collection_name = collection_name,
            scroll_filter = scroll_filter,
            limit = limit
        )
        return hits
    except Exception as e:
        print(e)
        return []

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

def create_document_packet(
    document: any,
    configuration: any,
) -> any:
    document_type = document['type']
    used_configuration = configuration[document_type]
    
    document_chunks = []
    if document_type == 'python':
        document_chunks = langchain_create_code_chunks(
            language = used_configuration['language'],
            chunk_size = used_configuration['chunk-size'],
            chunk_overlap = used_configuration['chunk-overlap'],
            document = document['data']
        )
    if document_type == 'text' or document_type == 'yaml' or document_type == 'markdown':
        document_chunks = langchain_create_text_chunks(
            chunk_size = used_configuration['chunk-size'],
            chunk_overlap = used_configuration['chunk-overlap'],
            document = document['data']
        )
    # This needs to remove empty chunks
    filtered_chunks = []
    for chunk in document_chunks:
        if chunk.strip():
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
    document_chunk: any
) -> any:
    chunk = re.sub(r'[^\w\s]', '', document_chunk)
    chunk = re.sub(r'\s+', ' ', chunk) 
    chunk = chunk.strip()
    chunk = chunk.lower()
    # This helps to remove unique hashes for duplicates such as:
    # task_id = task_id )
    # task_id = task_id 
    # task_id = task_id )
    return chunk

def generate_chunk_hash(
    document_chunk: any
) -> any:
    cleaned_chunk = format_chunk(
        document_chunk = document_chunk
    )
    return hashlib.md5(cleaned_chunk.encode('utf-8')).hexdigest()

def generate_document_vectors(
    qdrant_client: any,
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

        chunk_hash = generate_chunk_hash(
            document_chunk = chunk
        )
        
        existing_chunks = qdrant_search_data(
            qdrant_client = qdrant_client,
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

def create_document_vectors(
    qdrant_client: any,
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
        document_packet = create_document_packet(
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
        qdrant_client = qdrant_client
    )
    
    collection_created = None
    if not vector_collection in vector_collections:
        collection_configuration = VectorParams(
            size = len(document_embeddings[0]), 
            distance = Distance.COSINE
        )
        collection_created = qdrant_create_collection(
            qdrant_client = qdrant_client,
            collection_name = vector_collection,
            configuration = collection_configuration
        )

    vector_points = generate_document_vectors(
        qdrant_client = qdrant_client,
        document_database = document_database,
        document_collection = document_collection,
        document_type = document_type,
        document_id = document_id,
        document_chunks = document_chunks,
        document_embeddings = document_embeddings,
        vector_collection = vector_collection
    )

    return vector_points

def store_vectors(
    minio_client: any,
    qdrant_client: any,
    configuration: any,
    storage_documents: any
):
    print('Storing vectors')
    
    used_object_bucket = configuration['object-bucket']
    used_object_path = configuration['object-path']
    
    identities_exists = minio_check_object(
        minio_client = minio_client,
        bucket_name = used_object_bucket, 
        object_path = used_object_path
    )

    document_identities = []
    # doesn't work
    if not len(identities_exists) == 0:
        document_identities = minio_get_object_data_and_metadata(
            minio_client = minio_client,
            bucket_name = used_object_bucket, 
            object_path = used_object_path
        )['data']
    
    amount_of_databases = len(storage_documents)
    database_index = 1
    for document_database, document_collections in storage_documents.items():
        vector_collection = document_database.replace('|','-') + '-embeddings'
        amount_of_collections = len(document_collections)
        collection_index = 1
        database_vectors = []
        for document_collection, documents in document_collections.items():
            #amount_of_documents = len(documents)
            for document in documents:
                document_identity = document_database + '-' + document_collection + '-' + str(document['_id'])

                if document_identity in document_identities:
                    continue
                    
                document_vectors = create_document_vectors(
                    qdrant_client = qdrant_client,
                    document_database = document_database,
                    document_collection = document_collection,
                    document = document,
                    configuration = configuration,
                    vector_collection = vector_collection
                )

                if 0 < len(document_vectors):
                    database_vectors.extend(document_vectors)
                    document_identities.append(document_identity)
            print('Collections: ' + str(collection_index) + '|' + str(amount_of_collections))
            collection_index += 1

        points_stored = qdrant_upsert_points(
            qdrant_client = qdrant_client, 
            collection_name = vector_collection,
            points = database_vectors
        )
        print('Databases: ' + str(database_index) + '|' + str(amount_of_databases))
        database_index += 1

    minio_create_or_update_object(
        minio_client = minio_client,
        bucket_name = used_object_bucket, 
        object_path = used_object_path,
        data = document_identities, 
        metadata = {}
    )
    
    print('Vectors stored')

def spacy_find_keywords(
    text: str
):   
    nlp = spacy.load("en_core_web_sm")
    formatted = nlp(text.lower())
    
    keywords = [
        token.lemma_ for token in formatted
        if not token.is_stop               
        and not token.is_punct              
        and not token.is_space              
        and len(token) > 1                  
    ]
    
    keywords = list(set(keywords))
    
    return keywords

def meili_is_client(
    storage_client: any
) -> any:
    try:
        return isinstance(storage_client, ms.Connection)
    except Exception as e:
        print(e)
        return False

def meili_setup_client(
    api_key: str,
    host: str
) -> any:
    try:
        meili_client = ms.Client(
            url = host, 
            api_key = api_key
        )
        return meili_client 
    except Exception as e:
        print(e)
        return None

def meili_get_index( 
    meili_client: any, 
    index_name: str
) -> any:
    try:
        index = meili_client.index(
            uid = index_name
        )
        return index
    except Exception as e:
        print(e)
        return None
    
def meili_check_index(
    meili_client: any, 
    index_name: str
) -> bool:
    try:
        meili_client.get_index(
            uid = index_name
        )
        return True
    except Exception as e:
        print(e)
        return False
    
def meili_remove_index(
    meili_client: any, 
    index_name: str
) -> bool:
    try:
        response = meili_client.index(
            index_name = index_name
        ).delete()
        return response
    except Exception as e:
        print(e)
        return None
    
def meili_list_indexes(
    meili_client: any
) -> bool:
    try:
        names = []
        indexes = meili_client.get_indexes()
        for index in indexes['results']:
            names.append(index.uid)
        return names
    except Exception as e:
        print(e)
        return None

def meili_add_documents(
    meili_client: any, 
    index_name: str, 
    documents: any
) -> any:
    try:
        index = meili_get_index(
            meili_client = meili_client,
            index_name = index_name
        )
        response = index.add_documents(
            documents = documents
        )
        return response
    except Exception as e:
        print(e)
        return None

def meili_set_filterable(
    meili_client: any, 
    index_name: str, 
    attributes: any
) -> any:
    try:
        index = meili_get_index(
            meili_client = meili_client,
            index_name = index_name
        )
        response = index.update_filterable_attributes(attributes)
        return response
    except Exception as e:
        print(e)
        return None

def meili_search_documents(
    meili_client: any, 
    index_name: str, 
    query: any, 
    options: any
) -> any:
    try:
        index = meili_get_index(
            meili_client = meili_client,
            index_name = index_name
        )
        response = index.search(
            query,
            options
        )
        return response
    except Exception as e:
        print(e)
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
        print(e)
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
        print(e)
        return None

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
    
def store_keywords(
    minio_client: any,
    meili_client: any,
    configuration: any,
    storage_documents: any
):
    print('Storing keywords')

    used_object_bucket = configuration['object-bucket']
    used_object_path = configuration['object-path']
    
    identities_exists = minio_check_object(
        minio_client = minio_client,
        bucket_name = used_object_bucket, 
        object_path = used_object_path
    )

    document_identities = []
    # doesn't work
    if not len(identities_exists) == 0:
        document_identities = minio_get_object_data_and_metadata(
            minio_client = minio_client,
            bucket_name = used_object_bucket, 
            object_path = used_object_path
        )['data']

    amount_of_databases = len(storage_documents)
    database_index = 1
    for document_database, collections in storage_documents.items():
        keyword_collection = document_database.replace('|','-') + '-keywords'
        database_keywords = []
        collection_index = 1
        amount_of_collections = len(collections)
        for document_collection, documents in collections.items():
            document_index = 1
            for document in documents:
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
                    database_keywords.append(document_keywords)
                    document_identities.append(document_identity)
            print('Collections: ' + str(collection_index) + '|' + str(amount_of_collections))
            collection_index += 1
        #print(database_keywords)
        stored = meili_add_documents(
            meili_client = meili_client,
            index_name = keyword_collection,
            documents = database_keywords
        )

        meili_set_filterable(
            meili_client = meili_client, 
            index_name = keyword_collection, 
            attributes = ['keywords']
        )
        
        print('Databases: ' + str(database_index) + '|' + str(amount_of_databases))
        database_index += 1
        
    minio_create_or_update_object(
        minio_client = minio_client,
        bucket_name = used_object_bucket, 
        object_path = used_object_path,
        data = document_identities, 
        metadata = {}
    )

@ray.remote
def preprocess_data(
    document_client: any,
    object_client: any,
    vector_client: any,
    search_client: any,
    repository_owner: str,
    repository_name: str,
    configuration: any
):
    try:
        stored_documents = get_stored_documents(
            mongo_client = document_client,
            database_prefix = get_github_storage_prefix(
                repository_owner = repository_owner,
                repository_name = repository_name
            )
        )
        
        store_vectors(
            minio_client = object_client,
            qdrant_client = vector_client,
            configuration = configuration,
            storage_documents = stored_documents
        )

        store_keywords(
            minio_client = object_client,
            meili_client = search_client,
            configuration = configuration,
            storage_documents = stored_documents
        )
        
        return True
    except Exception as e:
        print(e)
        return False

if __name__ == "__main__":
    print('Starting ray job')
    print('Ray version is:' + str(ray.__version__))
    
    input = json.loads(sys.argv[1])

    storage_parameters = input['storage-parameters']
    data_parameters = input['data-parameters']

    mongo_client = mongo_setup_client(
        username = storage_parameters['mongo-username'],
        password = storage_parameters['mongo-password'],
        address = storage_parameters['mongo-address'],
        port = storage_parameters['mongo-port']
    )

    minio_client = setup_minio(
        endpoint = storage_parameters['minio-endpoint'],
        username = storage_parameters['minio-username'],
        password = storage_parameters['minio-password']
    )

    qdrant_client = qdrant_setup_client(
        api_key = storage_parameters['qdrant-key'],
        address = storage_parameters['qdrant-address'], 
        port = storage_parameters['qdrant-port']
    )

    meili_client = meili_setup_client(
        api_key = storage_parameters['meili-key'],
        host = storage_parameters['meili-host']
    )

    github_token = data_parameters['github-token']
    repository_owner = data_parameters['repository-owner']
    repository_name = data_parameters['repository-name']
    relevant_files = data_parameters['relevant-files']
    configuration = data_parameters['configuration']

    fetch_store_status = ray.get(preprocess_data.remote(
        document_client = mongo_client,
        object_client = minio_client,
        vector_client = qdrant_client,
        search_client = meili_client,
        repository_owner = repository_owner,
        repository_name = repository_name,
        configuration = configuration
    ))

    print('Preprocess success:' + str(fetch_store_status))

    print('Ray job Complete')