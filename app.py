from utils.ai_agent.ai_agent import AIAgent, get_ai_agent
from utils.codemap import CodeWorkspaceClient

# TODO: store this in a DB
func_summary_map = {}

def generate_function_summaries(func, tree, ai_agent: AIAgent, workspace_client: CodeWorkspaceClient):
    print("generating for func: ", func)
    call_list = tree[func] if func in tree else []
    call_list_desc_map = {}
    if len(call_list):
        for call_func in call_list:
            if call_func not in func_summary_map:
                generate_function_summaries(call_func,tree, ai_agent, workspace_client)
                call_list_desc_map[call_func] = func_summary_map[call_func]

    function_code = workspace_client.fetch_function_code(func)
    func_summary_map[func] = ai_agent.get_function_summary(function_code, call_list_desc_map)
        

def main():
    # generate code tree
    workspace_client = CodeWorkspaceClient()
    code_tree = workspace_client.generate_code_tree_for_workspace()
    print("generated code tree:  \n", code_tree)

    # generate description for every function
    ai_agent = get_ai_agent(debug=False)
    for k, _ in code_tree.items():
        if k not in func_summary_map:
            generate_function_summaries(k, code_tree, ai_agent, workspace_client)
    
    # printing summaries
    for func, summary in func_summary_map.items():
        print(func, " : ", summary)

    # store the description in the vector database
    # take task input and convert into steps

if __name__ == '__main__':
    main()