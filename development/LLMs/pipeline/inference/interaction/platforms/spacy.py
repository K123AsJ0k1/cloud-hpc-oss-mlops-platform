
def spacy_search_keywords(
    language_model: any,
    text: str
):
    lowered = text.lower()
    formatted = language_model(lowered)
    
    keywords = [
        token.lemma_ for token in formatted
        if not token.is_stop               
        and not token.is_punct              
        and not token.is_space              
        and len(token) > 1                  
    ]
    
    keywords = list(set(keywords))
    
    return keywords