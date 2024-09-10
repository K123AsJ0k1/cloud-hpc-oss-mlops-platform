from bs4 import BeautifulSoup
import markdown
import nbformat
import requests
import requests
import time
import json
import re

def get_document_data(
    document_url: str,
    document_type: str
) -> any:
    data = None
    response = requests.get(
        url = document_url
    )
    if response.status_code == 200:
        if document_type == 'text':
            data = response.text
        if document_type == 'json':
            data = json.loads(response.text)
        # handle html later
    return data

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
        document = {
            'name': '',
            'data': ''
        }
        url_split = url.split('/')
        if 'github' in url_split[2]:
            if 'raw' in url_split[2]:
                file_end = url_split[-1].split('.')[-1]
                document['name'] = url_split[-1]
                if file_end in text_files:
                    document['data'] = get_document_data(
                        document_url = url,
                        document_type = 'text' 
                    )
                if file_end in json_files:
                    document['data'] = get_document_data(
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
    markdown_text: any
) -> any:
    html = markdown.markdown(markdown_text)
    soup = BeautifulSoup(html, features='html.parser')
    text = soup.get_text()
    code_block_pattern = re.compile(r"```")
    text = re.sub(code_block_pattern, '', text)
    text = text.rstrip('\n')
    text = text.replace('\nsh', '\n')
    text = text.replace('\nbash', '\n')
    return text

def create_python_documents(
    python_document: any
): 
    joined_code = ''.join(python_document)
    block_code_documents = tree_create_python_code_and_function_documents(
        code_document = joined_code
    )

    code_documents = []
    seen_function_names = []
    code_doc_index = 0
    for code_doc in block_code_documents:
        row_split = code_doc.split('\n')
        for row in row_split:
            if 'function' in row and 'code' in row:
                function_name = row.split(' ')[1]
                if not function_name in seen_function_names:
                    seen_function_names.append(function_name)
                else:
                    del block_code_documents[code_doc_index]
        code_doc_index += 1

    if 0 < len(block_code_documents):
        index = 1
        for code_doc in block_code_documents:
            code_documents.append({
                'index': index,
                'data': code_doc
            })
            index += 1
        
    formatted_documents = {
        'code': code_documents
    }
    return formatted_documents

def create_notebook_documents(
    notebook_document: any
):
    notebook_documents = extract_jupyter_notebook_markdown_and_code(
        notebook_document = notebook_document
    )

    markdown_documents = []
    for block in notebook_documents['markdown']:
        joined_text = ''.join(block['data'])
        markdown_text = parse_markdown_into_text(
            markdown_text = joined_text
        )
        markdown_documents.append({
            'index': block['id'],
            'data': markdown_text
        })
        
    code_documents = []
    seen_function_names = []
    for block in notebook_documents['code']:
        joined_code = ''.join(block['data'])
        block_code_documents = tree_create_python_code_and_function_documents(
            code_document = joined_code
        )

        code_doc_index = 0
        for code_doc in block_code_documents:
            row_split = code_doc.split('\n')
            for row in row_split:
                if 'function' in row and 'code' in row:
                    function_name = row.split(' ')[1]
                    if not function_name in seen_function_names:
                        seen_function_names.append(function_name)
                    else:
                        del block_code_documents[code_doc_index]
            code_doc_index += 1
        
        if 0 < len(block_code_documents):
            sub_indexes = False
            if 1 < len(block_code_documents):
                sub_indexes = True
            index = 1
            for code_doc in block_code_documents:
                if sub_indexes:
                    code_documents.append({
                        'sub-index': index, 
                        'index': block['id'],
                        'data': code_doc
                    })
                else:
                    code_documents.append({ 
                        'index': block['id'],
                        'data': code_doc
                    })
                index += 1
            
    formatted_documents = {
        'markdown': markdown_documents,
        'code': code_documents
    }
    
    return formatted_documents