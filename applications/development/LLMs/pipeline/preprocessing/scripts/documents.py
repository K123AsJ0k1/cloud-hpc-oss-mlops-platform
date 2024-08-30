from bs4 import BeautifulSoup
import nbformat
import requests
import requests
import time
import json

def get_document(
    document_url: str,
    document_type: str
) -> any:
    document = None
    response = requests.get(
        url = document_url
    )
    if response.status_code == 200:
        if document_type == 'text':
            document = response.text
        if document_type == 'json':
            document = json.loads(response.text)
        # handle html later
    return document

def scrape_documents(
    url_list: any,
    timeout: int
) -> any:
    documents = []

    text_files = [
        'py',
        'md',
        'yaml',
        'sh'
    ]

    json_files = [
        'ipynb'
    ]
    index = 0
    for url in url_list:
        document = None
        url_split = url.split('/')
        if 'github' in url_split[2]:
            if 'raw' in url_split[2]:
                file_end = url_split[-1].split('.')[-1]
                if file_end in text_files:
                    document = get_document(
                        document_url = url,
                        document_type = 'text' 
                    )
                if file_end in json_files:
                    document = get_document(
                        document_url = url,
                        document_type = 'json' 
                    )
        documents.append(document)
        index = index + 1
        if index < len(url_list):
            time.sleep(timeout)
    return documents