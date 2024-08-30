import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer

nltk.download('punkt_tab')
nltk.download('stopwords')

def get_code_document_keywords(
    code_document: any
):
    stemmer = PorterStemmer()
    stop_words = set(stopwords.words('english'))

    code_text = code_document.lower()
    tokens = word_tokenize(code_text)
    tokens = [token for token in tokens if len(token) > 1]
    
    tokens = [token for token in tokens if token not in stop_words]
    tokens = [stemmer.stem(token) for token in tokens]
    tokens = list(dict.fromkeys(tokens))

    return tokens