import pandas as pd

def filter_hit_documents(
    configuration: any,
    hits: any
) -> any:
    df = pd.DataFrame(hits)
    ids_with_both = df.groupby('document')['source'].nunique()
    ids_with_both = ids_with_both[ids_with_both > 1].index
    filtered_df = df[df['document'].isin(ids_with_both)]
    return filtered_df

def match_hit_documents(
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
    hits: str,
    configuration: any
) -> any:
    filtered_df = filter_hit_documents(
        configuration = configuration,
        hits = hits
    )

    matched_df = match_hit_documents(
        configuration = configuration,
        filtered_df = filtered_df
    ) 

    context_documents = select_context_documents(
        configuration = configuration,
        matched_df = matched_df
    )
    
    return context_documents