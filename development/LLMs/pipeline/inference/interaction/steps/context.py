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