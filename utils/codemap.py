import re
import ast

def create_code_tree(code_str):
    funcs = {}

    # Parse the code string into an AST
    tree = ast.parse(code_str)

    def traverse(node, funcs, current_func=None):
        if isinstance(node, ast.FunctionDef):
            name = node.name
            funcs[name] = []
            for child_node in ast.iter_child_nodes(node):
                traverse(child_node, funcs, name)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
                if current_func is not None:
                    if func_name in funcs:
                        funcs[current_func].append(func_name)
                    else:
                        funcs[current_func].append(func_name + "*")
            elif isinstance(node.func, ast.Attribute):
                obj_name = node.func.value.id
                func_name = node.func.attr
                if current_func is not None:
                    if obj_name in funcs:
                        funcs[current_func].append(obj_name + "." + func_name)
                    else:
                        funcs[current_func].append(obj_name + ".*")
        else:
            for child_node in ast.iter_child_nodes(node):
                traverse(child_node, funcs, current_func)

    traverse(tree, funcs)

    # Remove duplicates and sort the called functions for each function
    result = {}
    for func_name, called_funcs in funcs.items():
        result[func_name] = sorted(list(set(called_funcs)))

    return result


def read_files(file_names):
    """
    Reads the contents of the files with the given names and returns them as a single string.
    """
    code_str = ""
    for file_name in file_names:
        with open(file_name, "r") as f:
            code_str += f.read() + "\n"
    return code_str

# Read the code from multiple files into a single string
file_names = ["utils/solver.py"]
code_str = read_files(file_names)

# Create the code tree from the code string
code_tree = create_code_tree(code_str)

# filtering out variables and basic functions
filtered_tree = {}
basic_functions = ['abs', 'all', 'any', 'ascii', 'bin', 'bool', 'callable', 'chr', 'compile', 'complex', 'delattr', 'dict', 'dir', 'divmod', 'enumerate', 'eval', 'exec', 'filter', 'float', 'format', 'frozenset', 'getattr', 'globals', 'hasattr', 'hash', 'hex', 'id', 'input', 'int', 'isinstance', 'issubclass', 'iter', 'len', 'list', 'locals', 'map', 'max', 'memoryview', 'min', 'next', 'object', 'oct', 'open', 'ord', 'pow', 'print', 'property', 'range', 'repr', 'reversed', 'round', 'set', 'setattr', 'slice', 'sorted', 'staticmethod', 'str', 'sum', 'super', 'tuple', 'type', 'vars', 'zip']

for k, v in code_tree.items():
    if len(v):
        v = [s for s in v if not s.endswith('.*')]
        v = [s for s in v if not s[:-1] in basic_functions]
    filtered_tree[k] = v

print(filtered_tree)