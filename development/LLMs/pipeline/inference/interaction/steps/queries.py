import re

from platforms.langchain import langchain_chunk_prompt
from platforms.spacy import spacy_search_keywords

def format_prompt(
    text: str
) -> any:
    formatted = text.lower()
    formatted = re.sub(r'\s+', ' ', formatted)
    formatted = re.sub(r'[^\w\s]', '', formatted)
    formatted = formatted.strip()
    return formatted 

def create_queries(
    configuration: any,
    embedding_model: any,
    language_model: any,
    prompt: any
) -> any:
    chunks = langchain_chunk_prompt(
        configuration = configuration,
        prompt = prompt
    ) 

    embedding_queries = embedding_model.embed_documents(
        texts = chunks
    )

    keyword_queries = []
    for chunk in chunks:
        keywords = spacy_search_keywords(
            language_model = language_model,
            text = chunk
        )
        keyword_query = ' OR '.join([f'keywords = "{keyword}"' for keyword in keywords])
        keyword_queries.append(keyword_query)
    
    formatted_queries = {
        'embeddings': embedding_queries,
        'keywords': keyword_queries
    }
    
    return formatted_queries

def prompt_queries(
    configuration: any,
    embedding_model: any,
    language_model: any,
    prompt: str
) -> any:
    cleaned_prompt = format_prompt(
        prompt = prompt
    )

    queries = create_queries(
        configuration = configuration,
        embedding_model = embedding_model,
        language_model = language_model,
        prompt = cleaned_prompt
    )
    
    return queries