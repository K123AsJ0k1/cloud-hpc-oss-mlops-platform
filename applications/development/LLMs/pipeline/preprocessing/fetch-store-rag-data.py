import sys
import ray
import json

import re
import io
import pickle
import yaml 

import markdown
import nbformat

from github import Github

from pymongo import MongoClient as mc

from bs4 import BeautifulSoup

import tree_sitter_python as tspython
from tree_sitter import Language, Parser

from minio import Minio

from importlib.metadata import version

def pygithub_get_repo_paths(
    token: str,
    owner: str, 
    name: str
) -> any:
    g = Github(token)
    repo = g.get_repo(f"{owner}/{name}")
    contents = repo.get_contents("")
    paths = []
    while len(contents) > 0:
      file_content = contents.pop(0)
      if file_content.type == 'dir':
        contents.extend(repo.get_contents(file_content.path))
      else:
        paths.append(file_content.path)
    g.close()
    return paths

def pygithub_get_path_content(
    token: str,
    owner: str, 
    name: str, 
    path: str
) -> any:
    g = Github(token)
    repo = g.get_repo(f"{owner}/{name}")
    file_content = repo.get_contents(path)
    content = file_content.decoded_content.decode('utf-8')
    # fails on some yaml files
    # deployment/kubeflow/manifests/contrib/ray/kuberay-operator/base/resources.yaml
    # unsupported encoding: none
    g.close()
    return content

def mongo_is_client(
    storage_client: any
) -> any:
    return isinstance(storage_client, mc.Connection)

def mongo_setup_client(
    username: str,
    password: str,
    address: str,
    port: str
) -> any:
    connection_prefix = 'mongodb://(username):(password)@(address):(port)/'
    connection_address = connection_prefix.replace('(username)', username)
    connection_address = connection_address.replace('(password)', password)
    connection_address = connection_address.replace('(address)', address)
    connection_address = connection_address.replace('(port)', port)
    mongo_client = mc(
        host = connection_address
    )
    return mongo_client

def mongo_get_database(
    mongo_client: any,
    database_name: str
) -> any:
    try:
        database = mongo_client[database_name]
        return database
    except Exception as e:
        return None

def mongo_check_database(
    mongo_client: any, 
    database_name: str
) -> bool:
    try:
        database_exists = database_name in mongo_client.list_database_names()
        return database_exists
    except Exception as e:
        return False

def mongo_list_databases(
    mongo_client: any
) -> any:
    try:
        databases = mongo_client.list_database_names()
        return databases
    except Exception as e:
        return []

def mongo_remove_database(
    mongo_client: any, 
    database_name: str
) -> bool:
    try:
        mongo_client.drop_database(database_name)
        return True
    except Exception as e:
        return False

def mongo_get_collection(
    mongo_client: any, 
    database_name: str, 
    collection_name: str
) -> bool:
    try:
        database = mongo_get_database(
            mongo_client = mongo_client,
            database_name = database_name
        )
        collection = database[collection_name]
        return collection
    except Exception as e:
        return None
    
def mongo_check_collection(
    mongo_client: any, 
    database_name: any, 
    collection_name: any
) -> bool:
    try:
        database = mongo_client[database_name]
        collection_exists = collection_name in database.list_collection_names()
        return collection_exists
    except Exception as e:
        return False

def mongo_update_collection(
    mongo_client: any, 
    database_name: str, 
    collection_name: str, 
    filter_query: any, 
    update_query: any
) -> any:
    try:
        collection = mongo_get_collection(
            mongo_client = mongo_client, 
            database_name = database_name, 
            collection_name = collection_name
        )
        result = collection.update_many(filter_query, update_query)
        return result
    except Exception as e:
        return None

def mongo_list_collections(
    mongo_client: any, 
    database_name: str
) -> bool:
    try:
        database = mongo_get_database(
            mongo_client = mongo_client,
            database_name = database_name
        )
        collections = database.list_collection_names()
        return collections
    except Exception as e:
        return []

def mongo_remove_collection(
    mongo_client: any, 
    database_name: str, 
    collection_name: str
) -> bool:
    try: 
        database = mongo_get_database(
            mongo_client = mongo_client,
            database_name = database_name
        )
        database.drop_collection(collection_name)
        return True
    except Exception as e:
        return False

def mongo_create_document(
    mongo_client: any, 
    database_name: str, 
    collection_name: str, 
    document: any
) -> any:
    try: 
        collection = mongo_get_collection(
            mongo_client = mongo_client, 
            database_name = database_name, 
            collection_name = collection_name
        )
        result = collection.insert_one(document)
        return result
    except Exception as e:
        return None

def mongo_get_document(
    mongo_client: any, 
    database_name: str, 
    collection_name: str, 
    filter_query: any
):
    try: 
        collection = mongo_get_collection(
            mongo_client = mongo_client, 
            database_name = database_name, 
            collection_name = collection_name
        )
        document = collection.find_one(filter_query)
        return document
    except Exception as e:
        print(e)
        return None 

def mongo_list_documents(
    mongo_client: any, 
    database_name: str, 
    collection_name: str, 
    filter_query: any,
    sorting_query: any
) -> any:
    try: 
        collection = mongo_get_collection(
            mongo_client = mongo_client, 
            database_name = database_name, 
            collection_name = collection_name
        )
        documents = list(collection.find(filter_query).sort(sorting_query))
        return documents
    except Exception as e:
        return []

def mongo_update_document(
    mongo_client: any, 
    database_name: any, 
    collection_name: any, 
    filter_query: any, 
    update_query: any
) -> any:
    try: 
        collection = mongo_get_collection(
            mongo_client = mongo_client, 
            database_name = database_name, 
            collection_name = collection_name
        )
        result = collection.update_one(filter_query, update_query)
        return result
    except Exception as e:
        return None

def mongo_remove_document(
    mongo_client: any, 
    database_name: str, 
    collection_name: str, 
    filter_query: any
) -> bool:
    try: 
        collection = mongo_get_collection(
            mongo_client = mongo_client, 
            database_name = database_name, 
            collection_name = collection_name
        )
        result = collection.delete_one(filter_query)
        return result
    except Exception as e:
        return None
    
def is_minio_client(
    storage_client: any
) -> bool:
    return isinstance(storage_client, Minio)

def setup_minio(
    endpoint: str,
    username: str,
    password: str
) -> any:
    minio_client = Minio(
        endpoint = endpoint, 
        access_key = username, 
        secret_key = password,
        secure = False
    )
    return minio_client

def pickle_data(
    data: any
) -> any:
    pickled_data = pickle.dumps(data)
    length = len(pickled_data)
    buffer = io.BytesIO()
    buffer.write(pickled_data)
    buffer.seek(0)
    return buffer, length

def unpickle_data(
    pickled: any
) -> any:
    return pickle.loads(pickled)

def minio_create_bucket(
    minio_client: any,
    bucket_name: str
) -> bool: 
    try:
        minio_client.make_bucket(
            bucket_name = bucket_name
        )
        return True
    except Exception as e:
        print('MinIO bucket creation error')
        print(e)
        return False
    
def minio_check_bucket(
    minio_client: any,
    bucket_name:str
) -> bool:
    try:
        status = minio_client.bucket_exists(
            bucket_name = bucket_name
        )
        return status
    except Exception as e:
        print('MinIO bucket checking error')
        print(e)
        return False 
       
def minio_delete_bucket(
    minio_client: any,
    bucket_name:str
) -> bool:
    try:
        minio_client.remove_bucket(
            bucket_name = bucket_name
        )
        return True
    except Exception as e:
        print('MinIO bucket deletion error')
        print(e)
        return False
# Works
def minio_create_object(
    minio_client: any,
    bucket_name: str, 
    object_path: str, 
    data: any,
    metadata: dict
) -> bool: 
    # Be aware that MinIO objects have a size limit of 1GB, 
    # which might result to large header error    
    
    try:
        buffer, length = pickle_data(
            data = data
        )

        minio_client.put_object(
            bucket_name = bucket_name,
            object_name = object_path,
            data = buffer,
            length = length,
            metadata = metadata
        )
        return True
    except Exception as e:
        print('MinIO object creation error')
        print(e)
        return False
# Works
def minio_check_object(
    minio_client: any,
    bucket_name: str, 
    object_path: str
) -> any: 
    try:
        object_info = minio_client.stat_object(
            bucket_name = bucket_name,
            object_name = object_path
        )      
        return object_info
    except Exception as e:
        return {}
# Works
def minio_delete_object(
    minio_client: any,
    bucket_name: str, 
    object_path: str
) -> bool: 
    try:
        minio_client.remove_object(
            bucket_name = bucket_name, 
            object_name = object_path
        )
        return True
    except Exception as e:
        print('MinIO object deletion error')
        print(e)
        return False
# Works
def minio_update_object(
    minio_client: any,
    bucket_name: str, 
    object_path: str, 
    data: any,
    metadata: dict
) -> bool:  
    remove = minio_delete_object(
        minio_client = minio_client,
        bucket_name = bucket_name,
        object_path = object_path
    )
    if remove:
        return minio_create_object(
            minio_client = minio_client, 
            bucket_name = bucket_name, 
            object_path = object_path, 
            data = data,
            metadata = metadata
        )
    return False
# works
def minio_create_or_update_object(
    minio_client: any,
    bucket_name: str, 
    object_path: str, 
    data: any, 
    metadata: dict
) -> bool:
    bucket_status = minio_check_bucket(
        minio_client = minio_client,
        bucket_name = bucket_name
    )
    if not bucket_status:
        creation_status = minio_create_bucket(
            minio_client = minio_client,
            bucket_name = bucket_name
        )
        if not creation_status:
            return False
    object_status = minio_check_object(
        minio_client = minio_client,
        bucket_name = bucket_name, 
        object_path = object_path
    )
    if not object_status:
        return minio_create_object(
            minio_client = minio_client,
            bucket_name = bucket_name, 
            object_path = object_path, 
            data = data, 
            metadata = metadata
        )
    else:
        return minio_update_object(
            minio_client = minio_client,
            bucket_name = bucket_name, 
            object_path = object_path, 
            data = data, 
            metadata = metadata
        )
# Works
def minio_get_object_list(
    minio_client: any,
    bucket_name: str,
    path_prefix: str
) -> any:
    try:
        objects = minio_client.list_objects(
            bucket_name = bucket_name, 
            prefix = path_prefix, 
            recursive = True
        )
        return objects
    except Exception as e:
        return None  
    
def minio_get_object_data_and_metadata(
    minio_client: any,
    bucket_name: str, 
    object_path: str
) -> any:
    try:
        given_object_data = minio_client.get_object(
            bucket_name = bucket_name, 
            object_name = object_path
        )
        
        # There seems to be some kind of a limit
        # with the amount of request a client 
        # can make, which is why this variable
        # is set here to give more time got the client
        # to complete the request

        given_data = unpickle_data(
            pickled = given_object_data.data
        )
        
        given_object_info = minio_client.stat_object(
            bucket_name = bucket_name, 
            object_name = object_path
        )
        
        given_metadata = given_object_info.metadata
        
        return {'data': given_data, 'metadata': given_metadata}
    except Exception as e:
        print('MinIO object fetching error')
        print(e)
        return None

def get_github_repo_documents(
    object_client: any,
    github_token: str,
    repository_owner: str,
    repository_name: str,
    object_bucket: str,
    repo_paths_object: str,
    relevant_files: any,
    replace: bool
) -> any:
    print('Fetching paths')

    object_exists = minio_check_object(
        minio_client = object_client,
        bucket_name = object_bucket, 
        object_path = repo_paths_object
    )
 
    repo_paths = []
    if replace == 'true' or not object_exists:
        print('Getting github paths')

        repo_paths = pygithub_get_repo_paths(
            token = github_token,
            owner = repository_owner, 
            name = repository_name
        )

        print('Storing paths')

        minio_create_or_update_object(
            minio_client = object_client,
            bucket_name = object_bucket, 
            object_path = repo_paths_object,
            data = repo_paths, 
            metadata = {}
        )

        print('Paths stored')
    else:
        print('Getting stored paths')
        repo_paths = minio_get_object_data_and_metadata(
            minio_client = object_client,
            bucket_name = object_bucket, 
            object_path = repo_paths_object
        )['data']

    print('Filtering paths')
    relevant_paths = []
    for path in repo_paths:
        path_split = path.split('/')
        file_end = path_split[-1].split('.')[-1].rstrip()
        if file_end in relevant_files:
            relevant_paths.append(path.rstrip())
    print('Paths filtered')

    formatted_paths = {
        'paths': relevant_paths
    }

    # consider how to store this to allas
    return formatted_paths

def create_markdown_documents(
    markdown_text: any
) -> any:
    html = markdown.markdown(markdown_text)
    soup = BeautifulSoup(html, features='html.parser')
    code_block_pattern = re.compile(r"```")
    
    documents = []
    document = ''
    index = 1
    for element in soup.descendants:
        if element.name in ['h2', 'h3', 'h4', 'h5', 'h6']:
            text = element.get_text(strip = True)
            if not document == '':
                document = document.replace('\n', '')
                if not len(document.split()) == 1:
                    documents.append({
                        'index': index,
                        'sub-index': 0,
                        'type': 'markdown',
                        'data': document
                    })
                    index += 1
                document = ''
            document += text
        elif element.name == 'p':
            text = element.get_text(strip = True)
            text = re.sub(code_block_pattern, '', text)
            text = text.rstrip('\n')
            text = text.replace('\nsh', '')
            text = text.replace('\nbash', '')
            document += ' ' + text
        elif element.name in ['ul', 'ol']:
            text = ''
            for li in element.find_all('li'):
                item = li.get_text(strip=True)
                if not '-' in item:
                    text += '-' + item
                    continue
                text += item
            document += ' ' + text
            
    documents.append({
        'index': index,
        'sub-index': 0,
        'type': 'markdown',
        'data': document
    })
    
    formatted_documents = {
        'text': documents
    }
    
    return formatted_documents

def extract_yaml_values(
    section: any,
    path: str,
    values: any
) -> any:
    for key, value in section.items():
        if path == '':
            current_path = key
        else:
            current_path = path + '/' + key
        if isinstance(value, dict):
            extract_yaml_values(
                section = value,
                path = current_path,
                values = values
            )
        if isinstance(value, list):
            number = 1
            
            for case in value:
                base_path = current_path
                if isinstance(case, dict):
                   extract_yaml_values(
                       section = case,
                       path = current_path,
                       values = values
                   ) 
                   continue
                base_path += '/' + str(number)
                number += 1
                values.append(base_path + '=' + str(case))
        else:
            if isinstance(value, dict):
                continue
            if isinstance(value, list):
                continue
            values.append(current_path + '=' + str(value))
            
    return values

def create_yaml_documents(
    yaml_text: any
) -> any:
    # has problems with some yaml files
    # unsupported encoding: none
    # deployment/kubeflow/manifests/apps/kfp-tekton/upstream/v1/third-party/tekton/upstream/manifests/base/tektoncd-install/tekton-controller.yaml
    # 'list' object has no attribute 'items'
    # deployment/kubeflow/manifests/apps/kfp-tekton/upstream/v1/third-party/tekton/upstream/manifests/base/tektoncd-install/tekton-release.yaml
    # 'NoneType' object has no attribute 'items'
    # deployment/kubeflow/manifests/apps/kfp-tekton/upstream/v1/base/metadata/overlays/db/kustomization.yaml
    #   could not determine a constructor for the tag 'tag:yaml.org,2002:value'
    # in "<unicode string>", line 41, column 18:
    #      delimiter: =
    yaml_data = list(yaml.safe_load_all(yaml_text))

    documents = []
    index = 1
    for data in yaml_data:
        yaml_values = extract_yaml_values(
            section = data,
            path = '',
            values = []
        )

        previous_root = ''
        document = ''
        sub_index = 1
        for value in yaml_values:
            equal_split = value.split('=')
            path_split = equal_split[0].split('/')
            root = path_split[0]
            if not root == previous_root:
                if 0 < len(document):
                    documents.append({
                        'index': index,
                        'sub-index': sub_index,
                        'type': 'yaml',
                        'data': document
                    })
                    sub_index += 1
                    
                previous_root = root
                document = value
            else:
                document += value
                
        documents.append({
            'index': index,
            'sub-index': sub_index,
            'type': 'yaml',
            'data': document
        })
        index += 1

    formatted_documents = {
        'text': documents
    }
            
    return formatted_documents

def tree_extract_imports(
    node: any, 
    code_text: str
) -> any:
    imports = []
    if node.type == 'import_statement' or node.type == 'import_from_statement':
        start_byte = node.start_byte
        end_byte = node.end_byte
        imports.append(code_text[start_byte:end_byte].decode('utf8'))
    for child in node.children:
        imports.extend(tree_extract_imports(child, code_text))
    return imports

def tree_extract_dependencies(
    node: any, 
    code_text: str
) -> any:
    dependencies = []
    for child in node.children:
        if child.type == 'call':
            dependency_name = child.child_by_field_name('function').text.decode('utf8')
            dependencies.append(dependency_name)
        dependencies.extend(tree_extract_dependencies(child, code_text))
    return dependencies

def tree_extract_code_and_dependencies(
    node: any,
    code_text: str
) -> any:
    codes = []
    if not node.type == 'function_definition':
        start_byte = node.start_byte
        end_byte = node.end_byte
        name = node.child_by_field_name('name')
        if name is None:
            code = code_text[start_byte:end_byte].decode('utf8')
            if not 'def' in code:
                dependencies = tree_extract_dependencies(node, code_text)
                codes.append({
                    'name': 'global',
                    'code': code,
                    'dependencies': dependencies
                })
    return codes

def tree_extract_functions_and_dependencies(
    node: any, 
    code_text: str
) -> any:
    functions = []
    if node.type == 'function_definition':
        start_byte = node.start_byte
        end_byte = node.end_byte
        name = node.child_by_field_name('name').text.decode('utf8')
        code = code_text[start_byte:end_byte].decode('utf8')
        dependencies = tree_extract_dependencies(node, code_text)
        functions.append({
            'name': name,
            'code': code,
            'dependencies': dependencies
        })
    for child in node.children:
        functions.extend(tree_extract_functions_and_dependencies(child, code_text))
    return functions

def tree_get_used_imports(
    general_imports: any,
    function_dependencies: any
) -> any:
    parsed_imports = {}
    for code_import in general_imports:
        import_factors = code_import.split('import')[-1].replace(' ', '')
        import_factors = import_factors.split(',')
    
        for factor in import_factors:
            if not factor in parsed_imports:
                parsed_imports[factor] = code_import.split('import')[0] + 'import ' + factor
            
    relevant_imports = {}
    for dependency in function_dependencies:
        initial_term = dependency.split('.')[0]
    
        if not initial_term in relevant_imports:
            if initial_term in parsed_imports:
                relevant_imports[initial_term] = parsed_imports[initial_term]
    
    used_imports = []
    for name, code in relevant_imports.items():
        used_imports.append(code)

    return used_imports

def tree_get_used_functions(
    general_functions: any,
    function_dependencies: any
): 
    used_functions = []
    for related_function_name in function_dependencies:
        for function in general_functions:
            if function['name'] == related_function_name:
                used_functions.append('from ice import ' + function['name'])
    return used_functions

def tree_create_code_document(
    code_imports: any,
    code_functions: any,
    function_item: any
) -> any:
    used_imports = tree_get_used_imports(
        general_imports = code_imports,
        function_dependencies = function_item['dependencies']
    )

    used_functions = tree_get_used_functions(
        general_functions = code_functions,
        function_dependencies = function_item['dependencies']
    )
    
    document = {
        'imports': used_imports,
        'functions': used_functions,
        'name': function_item['name'],
        'dependencies': function_item['dependencies'],
        'code': function_item['code']
    }
    
    return document
     
def tree_format_code_document(
    code_document: any
) -> any:
    formatted_document = ''
    for doc_import in code_document['imports']:
        formatted_document += doc_import + '\n'

    for doc_functions in code_document['functions']:
        formatted_document += doc_functions + '\n'

    if 0 < len(code_document['dependencies']):
        formatted_document += 'code dependencies\n'

        for doc_dependency in code_document['dependencies']:
            formatted_document += doc_dependency + '\n'

    if code_document['name'] == 'global':
        formatted_document += code_document['name'] + ' code\n'
    else:
        formatted_document += 'function ' + code_document['name'] + ' code\n'
    
    for line in code_document['code'].splitlines():
        if not bool(line.strip()):
            continue
        doc_code = re.sub(r'#.*','', line)
        if not bool(doc_code.strip()):
            continue
        formatted_document += doc_code + '\n'    
    return formatted_document

def tree_create_python_code_and_function_documents(
    code_document: any
):
    #print('Setup parser')
    PY_LANGUAGE = Language(tspython.language())
    parser = Parser(PY_LANGUAGE)

    #print('Parser setup')
   
    tree = parser.parse(
        bytes(
            code_document,
            "utf8"
        )
    )

    #print('Tree parsed')
    
    root_node = tree.root_node
    code_imports = tree_extract_imports(
        root_node, 
        bytes(
            code_document, 
            'utf8'
        )
    )

    #print('Imports parsed')
    
    code_global = tree_extract_code_and_dependencies(
        root_node, 
        bytes(
            code_document, 
            'utf8'
        )
    )

    #print('Global parsed')

    code_functions = tree_extract_functions_and_dependencies(
        root_node, 
        bytes(
            code_document, 
            'utf8'
        )
    )

    #print('Functions parsed')

    #print('Creating documents')
    initial_documents = []
    for item in code_global:
        document = tree_create_code_document(
            code_imports = code_imports,
            code_functions = code_functions,
            function_item = item
        )  
        initial_documents.append(document)

    for item in code_functions:
        document = tree_create_code_document(
            code_imports = code_imports,
            code_functions = code_functions,
            function_item = item
        )  
        initial_documents.append(document)

    #print('Formatting')
    formatted_documents = []
    seen_functions = []
    for document in initial_documents:
        if not document['name'] == 'global':
            if document['name'] in seen_functions:
                continue
        
        formatted_document = tree_format_code_document(
            code_document = document
        )

        formatted_documents.append(formatted_document)
        seen_functions.append(document['name'])
    #print('Formatted')
    return formatted_documents

def create_python_documents(
    python_text: any
): 
    #print('Create python documents')
    joined_code = ''.join(python_text)
    block_code_documents = tree_create_python_code_and_function_documents(
        code_document = joined_code
    )
    #print('Python blocks created')
    code_documents = []
    seen_function_names = []
    code_doc_index = 0
    for code_doc in block_code_documents:
        row_split = code_doc.split('\n')
        for row in row_split:
            if 'function' in row and 'code' in row:
                # This causes problems with some documents
                # list index out of range
                function_name = row.split(' ')[1]
                if not function_name in seen_function_names:
                    seen_function_names.append(function_name)
                else:
                    del block_code_documents[code_doc_index]
        code_doc_index += 1
    #print('Python blocks filtered')
    if 0 < len(block_code_documents):
        index = 1
        for code_doc in block_code_documents:
            code_documents.append({
                'index': index,
                'sub-index': 0,
                'type': 'python',
                'data': code_doc
            })
            index += 1
    #print('Formatting')
    formatted_documents = {
        'code': code_documents
    }
    return formatted_documents

def parse_jupyter_notebook_markdown_into_text(
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

def extract_jupyter_notebook_markdown_and_code(
    notebook_text: any
): 
    notebook_documents = {
        'markdown': [],
        'code': []
    }

    notebook = nbformat.reads(notebook_text, as_version=2)
    index = 1
    for cell in notebook.worksheets[0].cells:
        if cell.cell_type == 'markdown':
            notebook_documents['markdown'].append({
                'id': index,
                'data': cell.source
            })
            index += 1
        if cell.cell_type == 'code':
            notebook_documents['code'].append({
                'id': index,
                'data': cell.input
            })
            index += 1
    
    return notebook_documents

def create_notebook_documents(
    notebook_text: any
):
    #print('Create notebook documents')
    notebook_documents = extract_jupyter_notebook_markdown_and_code(
        notebook_text = notebook_text
    )
    #print('Creating markdwon documents')
    markdown_documents = []
    for block in notebook_documents['markdown']:
        joined_text = ''.join(block['data'])
        markdown_text = parse_jupyter_notebook_markdown_into_text(
            markdown_text = joined_text
        )
        markdown_documents.append({
            'index': block['id'],
            'sub-index': 0,
            'type': 'markdown',
            'data': markdown_text
        })
    #print('Markdown documents created')
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
                    # This causes problems with some documents
                    # list index out of range
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
                        'index': block['id'],
                        'sub-index': index, 
                        'type': 'python',
                        'data': code_doc
                    })
                else:
                    code_documents.append({ 
                        'index': block['id'],
                        'sub-index': 0,
                        'type': 'python',
                        'data': code_doc
                    })
                index += 1
    #print('Formatting')
    formatted_documents = {
        'text': markdown_documents,
        'code': code_documents
    }
    
    return formatted_documents

def store_repository_path_documents(
    mongo_client: any,
    github_token: any,
    repository_owner: str,
    repository_name: str,
    repository_path: str,
    database_name: str,
    collection_name: str
):
    #print('Storing documents')
    collection_exists = mongo_check_collection(
        mongo_client = mongo_client, 
        database_name = database_name, 
        collection_name = collection_name
    )

    if collection_exists:
        return False

    target_content = ''
    try:
        target_content = pygithub_get_path_content(
            token = github_token,
            owner = repository_owner, 
            name = repository_name, 
            path = repository_path
        )
    except Exception as e:
        print(repository_path)
        print('Get content error')
        print(e)

    if target_content == '':
        return False

    path_split = repository_path.split('/')
    target_type = path_split[-1].split('.')[-1]
    
    target_documents = {}
    if target_type == 'md':
        try:
            target_documents = create_markdown_documents(
                markdown_text = target_content
            )
        except Exception as e:
            print(repository_path)
            print('Create markdown document error')
            print(e)
    if target_type == 'yaml':
        try:
            target_documents = create_yaml_documents(
                yaml_text = target_content
            )
        except Exception as e:
            print(repository_path)
            print('Create yaml document error')
            print(e)
    if target_type == 'py':
        try:
            target_documents = create_python_documents(
                python_text = target_content
            )
        except Exception as e:
            print(repository_path)
            print('Create python document error')
            print(e)
    if target_type == 'ipynb':
        try:
            target_documents = create_notebook_documents(
                notebook_text = target_content
            )
        except Exception as e:
            print(repository_path)
            print('Create notebook document error')
            print(e)
    if 0 < len(target_documents):
        for doc_type, docs in target_documents.items():
            for document in docs:
                result = mongo_create_document(
                    mongo_client = mongo_client,
                    database_name = database_name,
                    collection_name = collection_name,
                    document = document
                )
        return True
    return False

def get_github_storage_prefix(
    repository_owner: str,
    repository_name: str
) -> str:
    return repository_owner + '|' + repository_name + '|'

def store_github_repository_documents(
    mongo_client: any,
    github_token: str,
    repository_owner: str,
    repository_name: str,
    repository_paths: any
) -> any:
    #print('Storing repository documents')
    paths = repository_paths['paths']
    for path in paths:
        path_split = path.split('/')
        document_database_name = get_github_storage_prefix(repository_owner, repository_name) + path_split[-1].split('.')[-1]
        
        document_collection_name = ''
        for word in path_split[:-1]:
            document_collection_name += word[:2] + '|'
        document_collection_name += path_split[-1].split('.')[0]

        stored = store_repository_path_documents(
            mongo_client = mongo_client,
            github_token = github_token,
            repository_owner = repository_owner,
            repository_name = repository_name,
            repository_path = path,
            database_name = document_database_name,
            collection_name = document_collection_name
        )
    #print('Documents stored')

@ray.remote
def fetch_and_store_data(
    storage_parameters: any,
    data_parameters: any
):
    try:
        print('Creating mongo client')
        document_client = mongo_setup_client(
            username = storage_parameters['mongo-username'],
            password = storage_parameters['mongo-password'],
            address = storage_parameters['mongo-address'],
            port = storage_parameters['mongo-port']
        )
        print('Mongo client created')

        print('Creating minio client')
        object_client = setup_minio(
            endpoint = storage_parameters['minio-endpoint'],
            username = storage_parameters['minio-username'],
            password = storage_parameters['minio-password']
        )
        print('Minio client created')
        
        github_token = data_parameters['github-token']
        repository_owner = data_parameters['repository-owner']
        repository_name = data_parameters['repository-name']
        object_bucket = data_parameters['object-bucket']
        repo_paths_object = data_parameters['repo-paths-object']
        relevant_files = data_parameters['relevant-files']
        replace = data_parameters['replace']

        print('Getting repository paths')
        
        repository_paths = get_github_repo_documents(
            object_client = object_client,
            github_token = github_token,
            repository_owner = repository_owner,
            repository_name = repository_name,
            object_bucket = object_bucket,
            repo_paths_object = repo_paths_object,
            relevant_files = relevant_files,
            replace = replace
        )

        print('Storing repository documents')

        store_github_repository_documents(
            mongo_client = document_client,
            github_token = github_token,
            repository_owner = repository_owner, 
            repository_name = repository_name, 
            repository_paths = repository_paths
        )

        print('Documents stored')
        
        return True
    except Exception as e:
        print('Fetch and store error')
        print(e)
        return False

if __name__ == "__main__":
    print('Starting ray job')
    print('Python version is:' + str(sys.version))
    print('Ray version is:' + version('Ray'))
    print('PyGithub version is:' + version('PyGithub'))
    print('PyMongo version is:' + version('PyMongo'))
    print('Markdown version is:' + version('Markdown'))
    print('Tree-sitter version is:' + version('tree-sitter'))
    print('Tree-sitter-python version is:' + version('tree-sitter-python'))
    print('BeautifulSoup version is:' + version('beautifulsoup4'))
    print('NBformat version is:' + version('nbformat'))
    
    input = json.loads(sys.argv[1])

    storage_parameters = input['storage-parameters']
    data_parameters = input['data-parameters']

    print('Running fetch and store')
    
    fetch_store_status = ray.get(fetch_and_store_data.remote(
        storage_parameters = storage_parameters,
        data_parameters = data_parameters
    ))

    print('Fetch and store success:' + str(fetch_store_status))

    print('Ray job Complete')