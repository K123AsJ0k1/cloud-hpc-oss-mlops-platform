def store_scraped_documents(
    mongo_client: any,
    database_prefix: str,
    documents: any
):
    for document in documents:
        file_name = document['name']
        file_data = document['data']
        
        formatted_documents = {}
        if '.ipynb' in file_name:
            formatted_documents = create_notebook_documents(
                notebook_document = file_data
            )
            document_database_name = database_prefix + '-workflows'
        if '.py' in file_name:
            formatted_documents = create_python_documents(
                python_document = file_data
            )
            document_database_name = database_prefix + '-code'
        
        for doc_type, doc_data in formatted_documents.items():
            for document in doc_data:
                document_data = document['data']
                document_index = document['index']
                document_sub_index = 0

                if 'sub-index' in document:
                    document_sub_index = document['sub-index']
                
                result = mongo_create_document(
                    mongo_client = mongo_client,
                    database_name = document_database_name,
                    collection_name = file_name,
                    document = {
                        'index': int(document_index),
                        'sub-index': int(document_sub_index),
                        'type': doc_type,
                        'data': document_data
                    }
                )