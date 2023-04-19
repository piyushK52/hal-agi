from abc import ABC
import ast
import inspect
import os


class CodeWorkspaceClient:
    def __init__(self):
        # TODO: automatically pick everything from gitignore
        self.exclude_dirs = ['build', 'dist', '__pycache__', '.vscode', 'venv', '.git', '.DS_Store', 'videos']
        self.exclude_files = ['README.md', 'LICENSE.txt', '.env', '.env-example', '.gitignore', 'requirements.txt', '__init__.py', 'dev.yaml', 'generated_code.py']

    def create_code_tree(self, code_str):
        funcs = {}

        # parse the code string into an AST
        tree = ast.parse(code_str)

        def traverse(node, funcs, current_func=None, current_class=None):
            if isinstance(node, ast.FunctionDef):
                name = node.name
                if current_class is not None:
                    name = current_class + '.' + name
                funcs[name] = []
                for child_node in ast.iter_child_nodes(node):
                    traverse(child_node, funcs, name, current_class)
            elif isinstance(node, ast.ClassDef):
                # ignoring abstract and test classes
                if not any(inspect.isclass(base) and issubclass(base, ABC) for base in node.bases) and not node.name.startswith("Test"):
                    current_class = node.name
                    for child_node in ast.iter_child_nodes(node):
                        traverse(child_node, funcs, current_func, current_class)
                else:
                    current_class = None
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
                    traverse(child_node, funcs, current_func, current_class)

        traverse(tree, funcs)

        # remove duplicates and sort the called functions for each function
        result = {}
        for func_name, called_funcs in funcs.items():
            result[func_name] = sorted(list(set(called_funcs)))

        return result


    def read_files(self, file_names):
        code_str = ""
        for file_name in file_names:
            with open(file_name, "r") as f:
                code_str += f.read() + "\n"
        return code_str

    # TODO: make this function more generalized
    def list_files(self, start_path):
        exclude_dirs, exclude_files = self.exclude_dirs, self.exclude_files
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

    def generate_code_tree_for_workspace(self):
        workspace_file_list = list(self.list_files('./'))
        print("files in the workspace: ", workspace_file_list)

        # fetching the entire code in the workspace
        code_str = self.read_files(workspace_file_list)
        code_tree = self.create_code_tree(code_str)

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

        excluded_functions = ['__init__', 'main', 'generate_function_summaries']

        for k, v in code_tree.items():
            if len(v):
                v = [s for s in v if not s.endswith('.*') and (not s[:-1] in basic_functions) and s != k]
                v = [(s[:-1] if s[-1] == '*' else s) for s in v]
                for ef in excluded_functions:
                    if ef in v:
                        v.remove(ef)

            exclude = False
            for ef in excluded_functions:
                if ef in k:
                    exclude = True

            if not exclude:
                if k[-1] == '*':
                    k = k[:-1]
                filtered_tree[k] = v

        return filtered_tree


    def fetch_function_code(self, function_name, excluded_directory_list=None, excluded_file_list=None, directory_path='./'):
        if not excluded_file_list:
            excluded_file_list = self.exclude_files
        if not excluded_directory_list:
            excluded_directory_list = self.exclude_dirs
        
        # removing the class prefix
        if '.' in function_name:
            function_name = function_name.split('.')[-1]
        
        function_code = ''
        for root, dirs, files in os.walk(directory_path, topdown=True):
            dirs[:] = [d for d in dirs if d not in excluded_directory_list]
            for filename in files:
                if filename not in excluded_file_list:
                    file_path = os.path.join(root, filename)
                    with open(file_path, 'r') as file:
                        file_contents = file.read()
                        tree = ast.parse(file_contents)

                    for node in ast.walk(tree):
                        if (isinstance(node, ast.FunctionDef) or isinstance(node, ast.ClassDef)) and node.name == function_name:
                            first_line = ast.get_source_segment(file_contents, node).strip()
                            function_code += first_line + '\n'
                            for line in node.body:
                                function_code += ast.unparse(line) + '\n'
        return function_code
    
    def find_class_init(self, filepath, class_name):
        with open(filepath, "r") as f:
            source = f.read()
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) or isinstance(node, ast.Return):
                if isinstance(node.value, ast.Call):
                    if isinstance(node.value.func, ast.Name) and node.value.func.id == class_name:
                        return node.lineno, source.split("\n")[node.lineno - 1]
        return None

    def search_directory_for_class_init(self, dirname, class_name):
        for dirpath, dirnames, filenames in os.walk(dirname):
            if any(x in dirpath for x in self.exclude_dirs):
                continue
            for filename in filenames:
                if filename.endswith(".py"):
                    filepath = os.path.join(dirpath, filename)
                    result = self.find_class_init(filepath, class_name)
                    if result:
                        return result[1]

    def get_import_path(self, directory, class_name):
        for dirpath, dirnames, filenames in os.walk(directory):
            if any(x in dirpath for x in self.exclude_dirs):
                    continue
            for filename in filenames:
                if filename.endswith(".py"):
                    filepath = os.path.join(dirpath, filename)
                    with open(filepath, "r") as f:
                        source = f.read()
                    tree = ast.parse(source)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef) and node.name == class_name:
                            module_path = os.path.relpath(filepath, directory)
                            module_path = module_path.replace(os.sep, ".")[:-3]
                            return f"from {module_path} import {class_name}"
        return None