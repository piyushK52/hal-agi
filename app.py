from repo.vector_repo.base import get_vector_db_client
from utils.ai_agent.ai_agent import AIAgent, get_ai_agent
from utils.codemap import CodeWorkspaceClient
from utils.solver import break_dict_by_length

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
    function_desc_map = {}
    for row in all_data:
        function_desc_map[row.function_name] = row.short_desc

    # task = input("enter task: ")
    # task = "write the code to take a text input and print a vector embedding generated from it"
    # task_list = ai_agent.get_task_breakup(task, {})
    # print('=> Task list generated')
    # for t in task_list:
    #     print(t)

    # function_desc_map_breakup_list = break_dict_by_length(function_desc_map, 2500)
    # required_functions = []
    # for func in function_desc_map_breakup_list:
    #     function_list = ai_agent.update_task_list_based_on_function_desc(task_list, func)
    #     if function_list and len(function_list):
    #         for helpful_function in function_list:
    #             if helpful_function != 'NONE':
    #                 required_functions.append(helpful_function)

    # print('=> Final list of important functions')
    # combined_instructions = ''
    # for t in required_functions:
    #     print(t)
    #     combined_instructions += t + '\n'
    
    combined_instructions = "get_text_embedding: This function can be used to generate a numerical representation of text for use in machine \
        learning algorithms. It can be used to achieve task 5 of generating vector embeddings for preprocessed text. Note: However, it is \
            important to note that the function get_text_embedding() may not use the specific pre-trained word embeddings model mentioned in \
            task 2, and may require modification to use the desired model. OpenAI.get_text_embedding: This function can be used to generate\
            embedding vectors for input text. No other function in the given code can be directly used to solve the task list. TestAIAgent.get_text_embedding: \
            This function can be used to generate an embedding vector representing the meaning of input text using the OpenAI API. \
            TestAIAgent.generate_short_desc: This function can be used to generate short descriptions for a given text using a query or\
            random selection.PgVectorDB: This class can be used for interacting with a PostgreSQL database table containing vector data, with \
            functions for CRUD operations and accessing the last entry ID. Specifically, the functions 'add_vector_data', 'fetch_similar_vector_data', \
            'fetch_all_data', and 'delete_vector' can be used for various database operations."

    combined_task_list = "1. Import the necessary libraries for generating vector embeddings such as spaCy or gensim\n\
        2. Load the pre-trained word embeddings model\n\
            3. Define a function to preprocess the text input by removing stop words, punctuations, and converting all words to lowercase\n\
                4. Apply the preprocessing function to the text input\n\
                    5. Generate the vector embedding for the preprocessed text using the pre-trained word embeddings model\n\
                        6. Print the vector embedding"
    
    base_query = 'use the following instructions to generate a new task list which make use of \
        the functions mentioned. Remove the tasks which are not needed or already covered in other tasks. ONLY return the task list: \n'
    query = 'given the task list: \n' + combined_task_list + '\n' + base_query + combined_instructions + '\n'
    context = [
            {"role": "system", "content": "You are AI coding assistant which returns the minimum number of tasks needed to complete a task list when useful functions are given"},
            {"role": "user", "content": 'given the task list: \n' + '1. import libraries to get weather data 2.get weather data 3. convert temperature into celcius 4. print temperature' + base_query\
             + 'fetch_weather_data: this provides weather information like temperature, humidity, and pressure'},
            {"role": "assistant", "content": "1. get temperature through fetch_weather_data 2. convert temperature into celcius 3. print temperature"},
            {"role": "user", "content": 'given the task list: \n' + '1. import libraries to get weather data 2.get weather data 3. convert temperature into celcius 4. print temperature' + base_query\
             + 'get_temperature: this provides temperature data in celcius'},
            {"role": "assistant", "content": "1. get temperature through get_temperature 2. print temperature"},
        ]
    res = ai_agent.get_query(query, context)
    print("\033[1;32mSuccess:\033[0m Task completed successfully.")
    print('=> Generated task list: \n', res['output'])
    task_list = res['output'].split('\n')

    # derive code for the steps
    # create a new code file
    with open("generated_code.py", "w") as f:
        print('=> Python file created')
        pass

    final_code = ''
    # index_of_empty = next((i for i, s in enumerate(task_list) if s == ""), len(task_list))
    # task_list = task_list[index_of_empty:]

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