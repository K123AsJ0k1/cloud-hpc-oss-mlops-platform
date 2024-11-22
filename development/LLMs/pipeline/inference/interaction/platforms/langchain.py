from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
)

def langchain_chunk_prompt(
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
    embedding_model: any,
    chunks: any
) -> any:  
    embeddings = embedding_model.embed_documents(
        texts = chunks
    )
    return embeddings