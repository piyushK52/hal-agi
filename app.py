from repo.vector_repo.base import get_vector_db_client
from utils.ai_agent.ai_agent import AIAgent, get_ai_agent
from utils.codemap import CodeWorkspaceClient

# TODO: store this in a DB
func_summary_map = {}

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
    use_open_ai_agent = False

    # generate code tree
    workspace_client = CodeWorkspaceClient()
    code_tree = workspace_client.generate_code_tree_for_workspace()
    print("generated code tree:  \n", code_tree)

    # generate description for every function
    ai_agent = get_ai_agent(debug=not use_open_ai_agent)
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
    from repo.vector_repo.pgvector import MyTable

    db_client = get_vector_db_client()
    for idx, (func, summary) in enumerate(func_summary_map.items()):
        summary_vector = ai_agent.get_text_embedding(summary)
        data = dict(id=idx, function_name=func, vector=summary_vector)
        db_client.add_vector_data([data])

    all_data = db_client.fetch_all_data()
    for row in all_data:
        print(row)


    # take task input and convert into steps
    # derive code for the steps

if __name__ == '__main__':
    main()