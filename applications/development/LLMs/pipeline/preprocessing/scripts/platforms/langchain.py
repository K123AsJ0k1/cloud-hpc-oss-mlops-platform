from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings

def langchain_generate_code_document_chunks(
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

    document_chunks = splitter.create_documents([document])
    document_chunks = [doc.page_content for doc in document_chunks]
    return document_chunks

def langchain_generate_document_chunk_embeddings(
    model_name: str,
    document_chunks: any
) -> any:
    embedding_model = HuggingFaceEmbeddings(
        model_name = model_name
    )
    chunk_embeddings = embedding_model.embed_documents(
        texts = document_chunks
    )
    return chunk_embeddings
