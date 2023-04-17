from repo.vector_repo.base import get_vector_db_client
from utils.ai_agent.ai_agent import AIAgent, get_ai_agent
from utils.codemap import CodeWorkspaceClient

func_summary_map = {}
func_short_summary_map = {}

def generate_function_summaries(func, tree, ai_agent: AIAgent, workspace_client: CodeWorkspaceClient):
    print("generating for func: ", func)
    call_list = tree[func] if func in tree else []
    func_name = func
    class_name = ''
    
    # separating class name
    if '.' in func:
        class_name, func_name = func.split('.')
        func_summary_map[class_name] = ''   # will update this after all the internal functions are summarized

    call_list_desc_map = {}
    if len(call_list):
        for call_func in call_list:
            if call_func not in func_summary_map:
                generate_function_summaries(call_func,tree, ai_agent, workspace_client)
                call_list_desc_map[call_func] = func_summary_map[call_func]

    function_code = workspace_client.fetch_function_code(func_name)
    func_summary_map[func] = ai_agent.get_function_summary(function_code, call_list_desc_map, class_name)


def main():
    # settings
    use_open_ai_agent = True

    workspace_client = CodeWorkspaceClient()
    ai_agent = get_ai_agent(debug=not use_open_ai_agent)
    db_client = get_vector_db_client()
    
    # TODO: change the logic here
    # only running the code below if the DB is empty
    all_data = db_client.fetch_all_data()
    if not len(all_data):
        # generate code tree
        code_tree = workspace_client.generate_code_tree_for_workspace()
        print("generated code tree:  \n", code_tree)

        # generate description for every function
        for k, _ in code_tree.items():
            if k not in func_summary_map:
                generate_function_summaries(k, code_tree, ai_agent, workspace_client)

        # generate description for every class
        func_key_list = func_summary_map.keys()
        for k, v in func_summary_map.items():
            if v == '':
                class_prefix = k + '.'
                class_methods = [func for func in func_key_list if func.startswith(class_prefix)]
                if len(class_methods):
                    class_method_desc = {}
                    for class_method in class_methods:
                        class_method_desc[class_method] = func_summary_map[class_method]

                    func_summary_map[k] = ai_agent.get_class_summary(k, '', class_method_desc)
                else:
                    # if no internal methods are present then fetching the entire class code
                    class_code = workspace_client.fetch_function_code(k)
                    func_summary_map[k] = ai_agent.get_class_summary(k, class_code, {})
        
        # printing summaries
        for func, summary in func_summary_map.items():
            print(func, " : ", summary)

        # store the description in the vector database
        for idx, (func, summary) in enumerate(func_summary_map.items()):
            summary_vector = ai_agent.get_text_embedding(summary)
            short_desc = ai_agent.generate_short_desc(summary)
            data = dict(function_name=func, vector=summary_vector, short_desc=short_desc)
            db_client.add_vector_data([data])

        all_data = db_client.fetch_all_data()
    
    # for row in all_data:
    #     print('data from db', row)

    # take task input and convert into steps
    # task = input("enter task: ")
    function_desc_map = {}
    for row in all_data:
        function_desc_map[row.function_name] = row.short_desc

    task = "write the code to take a text input and print a vector embedding generated from it"
    task_list = ai_agent.get_task_breakup(task, function_desc_map)
    print('=> Task list generated')
    for t in task_list:
        print(t)

    # derive code for the steps
    ## create a new code file
    with open("generated_code.py", "w") as f:
        print('=> Python file created')
        pass

    final_code = ''
    index_of_empty = next((i for i, s in enumerate(task_list) if s == ""), len(task_list))
    task_list = task_list[index_of_empty:]

    for task in task_list:
        task_embedding = ai_agent.get_text_embedding(task)
        top_similar_function = db_client.fetch_similar_vector_data(task_embedding, 3)
        function_code_list = {}
        for func in top_similar_function:
            function_code = workspace_client.fetch_function_code(func.function_name)
            function_code_list[func.function_name] = function_code

        generated_code = ai_agent.generate_task_code(task, function_code_list)

        while "help: " in generated_code:
            print('task - ', task)
            help_input = input('provide for info regarding this query: \n' + generated_code + ': ')
            generated_code = ai_agent.generate_task_code(task + 'given: ' + help_input, function_code_list)

        # adding the code to the file
        final_code += '\n'
        final_code += generated_code

    
    # fixing the code
    final_code = ai_agent.fix_code_issues(final_code)
    with open("generated_code.py", "w") as f:
        f.write("\n")
        f.write(final_code)


if __name__ == '__main__':
    main()