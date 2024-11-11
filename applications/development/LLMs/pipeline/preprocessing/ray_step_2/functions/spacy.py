
import spacy

def spacy_find_keywords(
    text: str
):   
    nlp = spacy.load("en_core_web_sm")
    formatted = nlp(text.lower())
    
    keywords = [
        token.lemma_ for token in formatted
        if not token.is_stop               
        and not token.is_punct              
        and not token.is_space              
        and len(token) > 1                  
    ]
    
    keywords = list(set(keywords))
    
    return keywords
