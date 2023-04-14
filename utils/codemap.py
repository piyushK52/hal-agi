import ast
import os

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
                if isinstance(node.func.value, ast.Name):
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
    code_str = ""
    for file_name in file_names:
        with open(file_name, "r") as f:
            code_str += f.read() + "\n"
    return code_str

# TODO: make this function more generalized
def list_files(start_path, exclude_dirs=None, exclude_files=None):
    if exclude_dirs is None:
        exclude_dirs = set()
    else:
        exclude_dirs = set(exclude_dirs)
    if exclude_files is None:
        exclude_files = set()
    else:
        exclude_files = set(exclude_files)
    for dirpath, dirnames, filenames in os.walk(start_path):
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
        filenames[:] = [f for f in filenames if f not in exclude_files and os.path.splitext(f)[1] == ".py"]
        for filename in filenames:
            yield os.path.join(dirpath, filename)

# TODO: automatically pick everything from gitignore
exclude_dirs = ['build', 'dist', '__pycache__', '.vscode', 'venv', '.git', '.DS_Store', 'videos']
exclude_files = ['README.md', 'LICENSE.txt', '.env', '.gitignore', 'requirements.txt', '__init__.py']
workspace_file_list = list(list_files('./', exclude_dirs, exclude_files))
print("files in the workspace: ", workspace_file_list)

# fetching the entire code in the workspace
code_str = read_files(workspace_file_list)
code_tree = create_code_tree(code_str)

# filtering out variables and basic functions
filtered_tree = {}
basic_functions = ['abs', 'all', 'any', 'ascii', 'bin', 'bool', 'callable', 'chr', 'compile', 'complex',\
                    'delattr', 'dict', 'dir', 'divmod', 'enumerate', 'eval', 'exec', 'filter', 'float',\
                          'format', 'frozenset', 'getattr', 'globals', 'hasattr', 'hash', 'hex', 'id', \
                            'input', 'int', 'isinstance', 'issubclass', 'iter', 'len', 'list', 'locals',\
                                  'map', 'max', 'memoryview', 'min', 'next', 'object', 'oct', 'open', 'ord',\
                                      'pow', 'print', 'property', 'range', 'repr', 'reversed', 'round', 'set',\
                                          'setattr', 'slice', 'sorted', 'staticmethod', 'str', 'sum', 'super', \
                                            'tuple', 'type', 'vars', 'zip']
excluded_func_list = ['__init__']

for k, v in code_tree.items():
    print(k, v)
    if len(v):
        v = [s for s in v if not s.endswith('.*') and (not s[:-1] in basic_functions) and s != k]
    filtered_tree[k] = v

print(filtered_tree)