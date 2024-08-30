from bs4 import BeautifulSoup
import markdown
import nbformat
import requests
import requests
import time
import json
import re

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

def extract_jupyter_notebook_markdown_and_code(
    notebook_document: any
): 
    notebook_documents = {
        'markdown': [],
        'code': []
    }

    notebook = nbformat.from_dict(notebook_document)

    index = 0
    for cell in notebook.cells:
        if cell.cell_type == 'markdown':
            notebook_documents['markdown'].append({
                'id': index,
                'data': cell.source
            })
            index += 1
        if cell.cell_type == 'code':
            notebook_documents['code'].append({
                'id': index,
                'data': cell.source
            })
            index += 1
    
    return notebook_documents
    
def parse_markdown_into_text(
    markdown_document: any
) -> any:
    markdown_text = ''.join(markdown_document)
    html = markdown.markdown(markdown_text)
    soup = BeautifulSoup(html, features='html.parser')
    text = soup.get_text()
    text = text.rstrip('\n')
    return text

def create_notebook_documents(
    notebook_document: any
):
    notebook_documents = extract_jupyter_notebook_markdown_and_code(
        notebook_document = notebook_document
    )

    markdown_document = ''
    markdown_ids = []
    for block in notebook_documents['markdown']:
        markdown_text = parse_markdown_into_text(
            markdown_document = block['data']
        )
        markdown_document += markdown_text + '\n\n'
        markdown_ids.append(block['id'])
    
    code_documents = []
    code_ids = []
    for block in notebook_documents['code']:
        block_code_documents = tree_created_python_function_documents(
            code_document = str(block['data'])
        )
        code_documents.extend(block_code_documents)
        code_ids.append(block['id'])
    
    formatted_documents = {
        'markdown': markdown_document,
        'code': code_documents
    }
    
    return formatted_documents