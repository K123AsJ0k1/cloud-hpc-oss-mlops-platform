import ray

@ray.remote(
    num_gpus = 1
)
class Generator:
    def __init__(
        self,
        embedding_model: str,
        keyword_model: str
    ):
        import torch
        from langchain_huggingface import HuggingFaceEmbeddings
        import spacy

        print('Starting generator')
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print('GPU device: ' + str(device))
        
        print('Embedding model setup')
        self.embedding_model = HuggingFaceEmbeddings(
            model_name = embedding_model,
            model_kwargs = {
                "device": device
            }
        )
        print('Embedding model ready')
        
        spacy.require_gpu()

        print('Language model setup')
        self.language_model = spacy.load(
            name = keyword_model
        )
        print('Language model ready')

    def batch_create_embeddings(
        self,
        chunk_batches_ref: any
    ) -> any:
        chunk_batches = ray.get(chunk_batches_ref)
        embedding_batches = []
        for chunk in chunk_batches:
            embedding = self.embedding_model.embed_documents(
                texts = chunk
            )
            embedding_batches.append(embedding)
        return embedding_batches
    
    def batch_search_keywords(
        self,
        text_batches_ref: str
    ):  
        text_batches = ray.get(text_batches_ref)
        keyword_batches = []
        for text in text_batches:
            lowered = text.lower()
            formatted = self.language_model(lowered)
            keywords = [
                token.lemma_ for token in formatted
                if not token.is_stop               
                and not token.is_punct              
                and not token.is_space              
                and len(token) > 1                  
            ]
            keywords = list(set(keywords))
            keyword_batches.append(keywords)
        return keyword_batches