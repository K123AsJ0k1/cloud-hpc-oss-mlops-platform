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