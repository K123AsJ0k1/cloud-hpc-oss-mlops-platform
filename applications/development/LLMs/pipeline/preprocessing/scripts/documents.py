import requests

def get_document(
    document_url: str
) -> any:
    document = None
    response = requests.get(
        url = document_url
    )
    if response.status_code == 200:
        document = response.text
    return document