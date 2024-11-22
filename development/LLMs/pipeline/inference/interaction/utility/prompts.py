import re
from langchain_text_splitters import (
    Language,
    RecursiveCharacterTextSplitter,
)
from langchain_huggingface import HuggingFaceEmbeddings

from platforms.spacy import spacy_find_keywords

def clean_prompt(
    prompt: str
) -> any:
    prompt = prompt.lower()
    prompt = re.sub(r'\s+', ' ', prompt)
    prompt = re.sub(r'[^\w\s]', '', prompt)
    return prompt.strip()

def chunk_prompt(
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
    
def generate_chunk_embedding_queries(
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

def generate_chunk_keyword_queries(
    chunks: any
) -> any:
    keyword_queries = []
    for chunk in chunks:
        keywords = spacy_find_keywords(
            text = chunk
        )
        keyword_query = ' OR '.join([f'keywords = "{keyword}"' for keyword in keywords])
        keyword_queries.append(keyword_query)
    return keyword_queries

def generate_prompt_queries(
    configuration: any,
    prompt: str
) -> any:
    cleaned_prompt = clean_prompt(
        prompt = prompt
    )
    
    prompt_chunks = chunk_prompt(
        configuration = configuration,
        prompt = cleaned_prompt
    ) 

    embedding_queries = generate_chunk_embedding_queries(
        configuration = configuration,
        chunks = prompt_chunks
    )

    keyword_queries = generate_chunk_keyword_queries(
        chunks = prompt_chunks
    )

    formatted_queries = {
        'embeddings': embedding_queries,
        'keywords': keyword_queries
    }

    return formatted_queries