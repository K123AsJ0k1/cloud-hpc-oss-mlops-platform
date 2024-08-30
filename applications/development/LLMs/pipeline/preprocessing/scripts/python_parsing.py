import tree_sitter_python as tspython
from tree_sitter import Language, Parser
import re

def extract_imports(
    node: any, 
    code_text: str
) -> any:
    imports = []
    if node.type == 'import_statement' or node.type == 'import_from_statement':
        start_byte = node.start_byte
        end_byte = node.end_byte
        imports.append(code_text[start_byte:end_byte].decode('utf8'))
    for child in node.children:
        imports.extend(extract_imports(child, code_text))
    return imports

def extract_dependencies(
    node: any, 
    code_text: str
) -> any:
    dependencies = []
    for child in node.children:
        if child.type == 'call':
            dependency_name = child.child_by_field_name('function').text.decode('utf8')
            dependencies.append(dependency_name)
        dependencies.extend(extract_dependencies(child, code_text))
    return dependencies
    
def extract_functions_and_dependencies(
    node: any, 
    code_text: str
) -> any:
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

