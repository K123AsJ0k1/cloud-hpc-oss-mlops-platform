import tree_sitter_python as tspython
from tree_sitter import Language, Parser
import re

# Created and works 
def extract_imports(node, code_text):
    imports = []
    if node.type == 'import_statement' or node.type == 'import_from_statement':
        start_byte = node.start_byte
        end_byte = node.end_byte
        imports.append(code_text[start_byte:end_byte].decode('utf8'))
    for child in node.children:
        imports.extend(extract_imports(child, code_text))
    return imports
# Created and works 
def extract_dependencies(node, code_text):
    dependencies = []
    for child in node.children:
        if child.type == 'call':
            dependency_name = child.child_by_field_name('function').text.decode('utf8')
            dependencies.append(dependency_name)
        dependencies.extend(extract_dependencies(child, code_text))
    return dependencies
# Created and works  
def extract_functions_and_dependencies(node, code_text):
    functions = []
    if node.type == 'function_definition':
        start_byte = node.start_byte
        end_byte = node.end_byte
        name = node.child_by_field_name('name').text.decode('utf8')
        code = code_text[start_byte:end_byte].decode('utf8')
        dependencies = extract_dependencies(node, code_text)
        functions.append({
            'name': name,
            'code': code,
            'dependencies': dependencies
        })
    for child in node.children:
        functions.extend(extract_functions_and_dependencies(child, code_text))
    return functions
# Created and works 
def get_used_imports(
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
# Created and works 
def get_used_functions(
    general_functions: any,
    function_dependencies: any
): 
    used_functions = []
    for related_function_name in function_dependencies:
        for function in general_functions:
            if function['name'] == related_function_name:
                used_functions.append('from ice import ' + function['name'])
    return used_functions
# Created and works 
def create_code_chunk(
    code_imports: any,
    code_functions: any,
    function_item: any
) -> any:
    used_imports = get_used_imports(
        general_imports = code_imports,
        function_dependencies = function_item['dependencies']
    )

    used_functions = get_used_functions(
        general_functions = code_functions,
        function_dependencies = function_item['dependencies']
    )
    
    chunk = {
        'imports': used_imports,
        'functions': used_functions,
        'name': function_item['name'],
        'dependencies': function_item['dependencies'],
        'code': function_item['code']
    }
    
    return chunk
# Created and works 
def format_code_chunk(
    code_chunk: any
) -> any:
    formatted_chunk = ''
    for chunk_import in code_chunk['imports']:
        formatted_chunk += chunk_import + '\n'

    for chunk_functions in code_chunk['functions']:
        formatted_chunk += chunk_functions + '\n'

    formatted_chunk += 'code dependencies\n'

    for chunk_dependency in code_chunk['dependencies']:
        formatted_chunk += chunk_dependency + '\n'
    
    for line in code_chunk['code'].splitlines():
        if not bool(line.strip()):
            continue
        parsed_code = re.sub(r'#.*','', line)
        if not bool(parsed_code.strip()):
            continue
        formatted_chunk += parsed_code + '\n'    
    return formatted_chunk
# Created and works 
def parse_python_code_chunks(
    document_code: any
):
    PY_LANGUAGE = Language(tspython.language())
    parser = Parser(PY_LANGUAGE)
   
    tree = parser.parse(
        bytes(
            document_code,
            "utf8"
        )
    )

    root_node = tree.root_node
    code_imports = extract_imports(
        root_node, 
        bytes(
            document_code, 
            'utf8'
        )
    )
    code_functions = extract_functions_and_dependencies(
        root_node, 
        bytes(
            document_code, 
            'utf8'
        )
    )
    
    initial_chunks = []
    for item in code_functions:
        chunk = create_code_chunk(
            code_imports = code_imports,
            code_functions = code_functions,
            function_item = item
        )  
        initial_chunks.append(chunk)

    formatted_chunks = []
    for chunk in initial_chunks:
        formatted_chunk = format_code_chunk(
            code_chunk = chunk
        )
        formatted_chunks.append(formatted_chunk)
    return formatted_chunks