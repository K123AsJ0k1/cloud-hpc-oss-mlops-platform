from typing import List, Union, Generator, Iterator
from schemas import OpenAIChatMessage
import subprocess
from pydantic import BaseModel

from pymongo import MongoClient as mc
from qdrant_client import QdrantClient as qc 
import meilisearch as ms 

import re
from langchain_text_splitters import (
    Language,
    RecursiveCharacterTextSplitter,
)
from langchain_huggingface import HuggingFaceEmbeddings

import spacy

import pandas as pd

from bson.objectid import ObjectId


class Pipeline:
    class Valves(BaseModel):
        MONGO_USER: str
        MONGO_PASSWORD: str 
        MONGO_ADDRESS: str
        MONGO_PORT: str
        QDRANT_KEY: str
        QDRANT_ADDRESS: str
        QDRANT_PORT: str    
        MEILI_HOST: str
        MEILI_KEY: str

    def __init__(
        self
    ):
        # Optionally, you can set the id and name of the pipeline.
        #self.id = "python_code_pipeline"
        #self.name = "Python Code Pipeline"
        #pass

        self.name = "RAG Pipeline"
        self.mongo_client = None
        self.qdrant_client = None
        self.meili_client = None

        self.valves = self.Valves(
            **{
                "pipelines": ["*"],                                                           
                "MONGO_USER": "mongo123",                     
                "MONGO_PASSWORD": "mongo456",                                         
                "MONGO_ADDRESS": "127.0.0.1",                                  
                "MONGO_PORT": "27017",                          
                "QDRANT_KEY": "qdrant_key",                          
                "QDRANT_ADDRESS": "127.0.0.1",                            
                "QDRANT_PORT": "6333", 
                "MEILI_HOST": "http://127.0.0.1:7700",
                "MEILI_KEY": "meili_key"          
            }
        )

    async def on_startup(
        self
    ):
        # This function is called when the server is started.
        #print(f"on_startup:{__name__}")
        pass

    async def on_shutdown(
        self
    ):
        # This function is called when the server is stopped.
        #print(f"on_shutdown:{__name__}")
        pass

    def mongo_setup_client(
        self,
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
        self,
        mongo_client: any,
        database_name: str
    ) -> any:
        try:
            database = mongo_client[database_name]
            return database
        except Exception as e:
            return None

    def mongo_get_collection(
        self,
        mongo_client: any, 
        database_name: str, 
        collection_name: str
    ) -> bool:
        try:
            database = self.mongo_get_database(
                mongo_client = mongo_client,
                database_name = database_name
            )
            collection = database[collection_name]
            return collection
        except Exception as e:
            return None
        
    def mongo_get_document(
        self,
        mongo_client: any, 
        database_name: str, 
        collection_name: str, 
        filter_query: any
    ):
        try: 
            collection = self.mongo_get_collection(
                mongo_client = mongo_client, 
                database_name = database_name, 
                collection_name = collection_name
            )
            document = collection.find_one(filter_query)
            return document
        except Exception as e:
            print(e)
            return None 

    def qdrant_setup_client(
        self,
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

    def qdrant_list_collections(
        self,
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

    def qdrant_search_vectors(
        self,
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

    def meili_setup_client(
        self,
        host: str, 
        api_key: str
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
        self,
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
        
    def meili_list_indexes(
        self,
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

    def meili_search_documents(
        self,
        meili_client: any, 
        index_name: str, 
        query: any, 
        options: any
    ) -> any:
        try:
            index = self.meili_get_index(
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

    def langchain_chunk_prompt(
        self,
        configuration: any,
        prompt: str
    ) -> any:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size = configuration['chunk-size'], 
            chunk_overlap = configuration['chunk-overlap'],
            length_function = len
        )

        prompt_chunks = splitter.create_documents([prompt])
        prompt_chunks = [prompt.page_content for prompt in prompt_chunks]
        return prompt_chunks
        
    def langchain_chunk_embeddings(
        self,
        configuration: any,
        chunks: any
    ) -> any:
        embedding_model = HuggingFaceEmbeddings(
            model_name = configuration['model-name']
        )    
        embeddings = embedding_model.embed_documents(
            texts = chunks
        )
        return embeddings

    def spacy_find_keywords(
        self,
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
    
    def spacy_create_chunk_keywords(
        self, 
        chunks: any
    ) -> any:
        keyword_queries = []
        for chunk in chunks:
            keywords = self.spacy_find_keywords(
                text = chunk
            )
            keyword_query = ' OR '.join([f'keywords = "{keyword}"' for keyword in keywords])
            keyword_queries.append(keyword_query)
        return keyword_queries
    
    def clean_prompt(
        self,
        prompt: str
    ) -> any:
        prompt = prompt.lower()
        prompt = re.sub(r'\s+', ' ', prompt)
        prompt = re.sub(r'[^\w\s]', '', prompt)
        return prompt.strip()

    def generate_prompt_queries(
        self,
        configuration: any,
        prompt: str
    ) -> any:
        cleaned_prompt = self.clean_prompt(
            prompt = prompt
        )
        
        prompt_chunks = self.langchain_chunk_prompt(
            configuration = configuration,
            prompt = cleaned_prompt
        ) 

        embedding_queries = self.langchain_chunk_embeddings(
            configuration = configuration,
            chunks = prompt_chunks
        )

        keyword_queries = self.spacy_create_chunk_keywords(
            chunks = prompt_chunks
        )

        formatted_queries = {
            'embeddings': embedding_queries,
            'keywords': keyword_queries
        }

        return formatted_queries

    def calculate_keyword_score(
        self,
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
        self,
        vector_client: any,
        configuration: any,
        embedding_queries: any
    ) -> any:
        recommeded_cases = []

        collections = self.qdrant_list_collections(
            qdrant_client = vector_client
        )
        for collection in collections:
            for embedding in embedding_queries:
                results = self.qdrant_search_vectors(
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
        self,
        search_client: any,
        configuration: any,
        keyword_queries: any
    ) -> any:
        recommeded_cases = []
        collections = self.meili_list_indexes(
            meili_client = search_client
        )
        
        for collection in collections:        
            for keywords in keyword_queries:
                results = self.meili_search_documents(
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
                    
                    
                    res_score = self.calculate_keyword_score(
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
        self,
        vector_client: any,
        search_client: any,
        configuration: any,
        queries: any
    ) -> any:
        vector_hits = self.get_vector_hits(
            vector_client = vector_client,
            configuration = configuration,
            embedding_queries = queries['embeddings']
        )
        
        search_hits = self.get_search_hits(
            search_client = search_client,
            configuration = configuration,
            keyword_queries = queries['keywords']
        )

        found_hits = vector_hits + search_hits

        return found_hits

    def filter_hit_documents(
        self,
        configuration: any,
        hits: any
    ) -> any:
        df = pd.DataFrame(hits)
        ids_with_both = df.groupby('document')['source'].nunique()
        ids_with_both = ids_with_both[ids_with_both > 1].index
        filtered_df = df[df['document'].isin(ids_with_both)]
        return filtered_df

    def match_hit_documents(
        self,
        configuration: any,
        filtered_df: any
    ) -> any:
        alpha = configuration['alpha']
        matched_documents = []
        for index_i, row_i in filtered_df[filtered_df['source'] == 'vector'].iterrows():
            vector_source = row_i['source']
            vector_database = row_i['database']
            vector_collection = row_i['collection']
            vector_id = row_i['document']
            vector_type = row_i['type']
            vector_score = row_i['score']
            
            for index_j, row_j in filtered_df[filtered_df['source'] == 'search'].iterrows():
                search_source = row_j['source']
                search_database = row_j['database']
                search_collection = row_j['collection']
                search_id = row_j['document']
                search_type = row_j['type']
                search_score = row_j['score']
                
                if vector_database == search_database:
                    if vector_collection == search_collection:
                        if vector_type == search_type:
                            if vector_id == search_id:
                                hybrid_score = vector_score * alpha + search_score * (1-alpha)
        
                                matched_documents.append({
                                    'source': 'hybrid',
                                    'database': search_database,
                                    'collection': search_collection,
                                    'document': search_id,
                                    'score': hybrid_score
                                })
        match_df = pd.DataFrame(matched_documents)
        return match_df

    def select_context_documents(
        self,
        configuration: any,
        matched_df: any
    ) -> any:
        sorted_df = matched_df.sort_values('score', ascending = False)
        seen_documents = []
        context_documents = []
        for row in sorted_df.values.tolist():
            row_id = row[3]
            if not row_id in seen_documents and len(context_documents) <= configuration['context-amount']:
                seen_documents.append(row_id)
                context_documents.append(row)
        return context_documents

    def get_top_documents(
        self,
        hits: str,
        configuration: any
    ) -> any:
        filtered_df = self.filter_hit_documents(
            configuration = configuration,
            hits = hits
        )

        matched_df = self.match_hit_documents(
            configuration = configuration,
            filtered_df = filtered_df
        ) 

        context_documents = self.select_context_documents(
            configuration = configuration,
            matched_df = matched_df
        )
        
        return context_documents

    def create_context(
        self,
        mongo_client: any,
        documents: any
    ) -> any:
        context = ''
        for metadata in documents:
            database = metadata[1]
            collection = metadata[2]
            document = metadata[3]
            data = self.mongo_get_document(
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
        self,
        document_client: any,
        vector_client: any,
        search_client: any,
        configuration: any,
        prompt: any
    ) -> any:

        print('Creating queries')

        prompt_query = self.generate_prompt_queries(
            configuration = configuration,
            prompt = prompt
        )

        print('Getting hits')

        prompt_hits = self.get_vector_search_hits(
            vector_client = vector_client,
            search_client = search_client,
            configuration = configuration,
            queries = prompt_query
        )
        
        print('Getting top documents')

        prompt_documents = self.get_top_documents(
            hits = prompt_hits,
            configuration = configuration
        ) 

        print('Creating context')

        prompt_context = self.create_context(
            mongo_client = document_client,
            documents = prompt_documents
        )

        return prompt_context

    def get_context(
        self,
        prompt: str
    ) -> str:
        
        print('Creating clients')
        mongo_client = self.mongo_setup_client(
            username = self.valves.MONGO_USER,
            password = self.valves.MONGO_PASSWORD,
            address = self.valves.MONGO_ADDRESS,
            port = self.valves.MONGO_PORT
        )

        qdrant_client = self.qdrant_setup_client(
            api_key = self.valves.QDRANT_KEY,
            address = self.valves.QDRANT_ADDRESS, 
            port = self.valves.QDRANT_PORT
        )

        meili_client = self.meili_setup_client(
            host = self.valves.MEILI_HOST, 
            api_key = self.valves.MEILI_KEY
        )
        print('Clients setup')

        pipeline_configuration = {
            'chunk-size': 50,
            'chunk-overlap': 0,
            'model-name': 'sentence-transformers/all-MiniLM-L6-v2',
            'top-k': 10,
            'alpha': 0.5,
            'context-amount': 5
        }

        print('Running context pipeline')
        created_context = self.context_pipeline(
            document_client = mongo_client,
            vector_client = qdrant_client,
            search_client = meili_client,
            configuration = pipeline_configuration ,
            prompt = prompt
        )
        print('Context pipeline run')

        return created_context

    def pipe(
        self, 
        user_message: str, 
        model_id: str, 
        messages: List[dict], 
        body: dict
    ) -> Union[str, Generator, Iterator]:

        print(f"pipe:{__name__}")

        print(messages)
        print(user_message)
        
        if body.get("title", False):
            print("Title Generation")
            return "Python Code Pipeline"
        else:
            context = self.get_context(
                prompt = user_message
            )
            #stdout, return_code = self.execute_python_code(user_message)
            return context