from abc import ABC
import time
import random
from typing import List
import re

from settings import FORCE_SUB_TASK_CREATION, OPENAI_API_KEY, VECTOR_EMBEDDING_DIM
from utils.ai_agent.constants import OpenAIModel


class AIAgent(ABC):
    def __init__(self):
        pass

    def get_query(self, query):
        pass

    def is_breakdown_of_task_needed(self, task: str):
        pass

    def breakdown_into_subtask(self, task: str):
        pass

    def solve_task(self, task: str):
        pass

    def get_function_summary(self, code: str, dict: dict, class_name: str):
        pass

    def get_class_summary(self, class_name, class_code, dict):
        pass

    def get_text_embedding(self, text):
        pass

    def get_task_breakup(self, query, func_desc_map):
        pass

    def generate_task_code(self, task, similar_func_code, class_init_code):
        pass

    def fix_code_issues(self, final_code):
        pass

    def generate_short_desc(self, function_summary):
        pass

    def update_task_list_based_on_function_desc(self, task_list, function_desc_map):
        pass

    def regenerate_task_list(self, combined_task_list, combined_instructions):
        pass

    def filter_numbered_list(self, task_list):
        pass


class OpenAI(AIAgent):
    def __init__(self):
        import openai

        self.openai = openai
        openai.api_key = OPENAI_API_KEY
        self.ai_model = OpenAIModel.gpt_turbo
        self.temperature = 0
        self.print_queries = True
        self._set_prompts()
    
    def _set_prompts(self):
        self.TASK_TYPE_PROMPT = "is this a general question, task or a greeting (answer only in \"general question\", \"task\", \"greeting\") - "
        self.IS_BREAKDOWN_REQUIRED_PROMPT = "Do this question needs to be broken into sub-tasks or it is trivial. Reply with only yes or no? - "
        self.BREAKDOWN_INTO_SUBTASK = "break this task in 3 or less sub-tasks (separated by ';'):\n"
        self.SOLVE_TASK_INPUT = "given the information :\n"
        self.SOLVE_TASK_QUESTION = "answer this: "

    def _generate_params(self, prompt, context: List=None):
        messages = context if context and len(context) else []
        messages.append({"role": "user", "content": prompt})

        return {
                "model": self.ai_model.model,
                "messages": messages,
                "temperature": self.temperature
            }
    
    def get_query(self, query, context=None):
        # removing random whitespaces 
        query = re.sub(' +', ' ', query)
        if context:
            for row in context:
                row["role"] = re.sub(' +', ' ', row["role"])
                row["content"] = re.sub(' +', ' ', row["content"])
        
        data = self._generate_params(query, context)

        if self.print_queries:
            print("\033[34mquery text\033[0m")
            print(query)
            print("\033[33mcontext\033[0m")
            print(context)

        start_time = time.time()
        try:
            response = self.openai.ChatCompletion.create(**data)
        except Exception as e:
            print("error occured: ", str(e))
            return None

        end_time = time.time()

        time_taken = round((end_time - start_time) * 1000, 6)   # in ms

        return {
            "token_usage": response["usage"]["total_tokens"],
            "time_taken": time_taken,
            "output": response["choices"][0]["message"]["content"] 
        }
    
    def is_breakdown_of_task_needed(self, task: str):
        if FORCE_SUB_TASK_CREATION:
            return True
        
        query = self.TASK_TYPE_PROMPT + task
        res = self.get_query(query)
        if 'greeting' in res['output']:
            return False
        
        query = self.IS_BREAKDOWN_REQUIRED_PROMPT + task
        res = self.get_query(query)
        return True if 'yes' in res['output'] else False

    def breakdown_into_subtask(self, task: str):
        query = self.BREAKDOWN_INTO_SUBTASK + task
        res = self.get_query(query)
        return res['output']
    
    def solve_task(self, task: str, data=None):
        query = ''
        if data:
            query += self.SOLVE_TASK_INPUT + data + '\n'

        query += self.SOLVE_TASK_QUESTION + task
        res = self.get_query(query)
        return res['output']
    
    def get_function_summary(self, code: str, call_list_desc_map, class_name):
        if not code:
            return ''
        
        func_call_list_query = ''
        if len(call_list_desc_map.keys()):
            for k, v in call_list_desc_map.items():
                func_call_list_query += f"{k} - {v}\n"
            
            func_call_list_query = 'Given the description of the following functions:\n' + func_call_list_query

        class_query = ''
        if class_name:
            class_query = f"Some further information, this function belongs to this class - {class_name} - "

        query = func_call_list_query + " describe what this function does:\n" + code + "\n" + class_query
        res = self.get_query(query)
        return res['output']
    
    def get_class_summary(self, class_name, class_code, call_list_desc_map):
        if not class_name:
            return ''
        
        class_method_list_query = ''
        if len(call_list_desc_map.keys()):
            for k, v in call_list_desc_map.items():
                class_method_list_query += f"{k} - {v}\n"
            
            class_method_list_query = 'Given the description of the following functions present in this class:\n' + class_method_list_query

        class_code_query = ''
        if not class_method_list_query:
            class_code_query = 'Given the following code of a class: ' + class_code
        
        if class_method_list_query:
            query = class_method_list_query + " describe what this class does:\n" + class_name
        else:
            query = class_code_query + " describe what this class does:\n" + class_name
        
        res = self.get_query(query)
        return res['output']
    
    def get_text_embedding(self, text):
        text = text.replace("\n", " ")
        model="text-embedding-ada-002"
        return self.openai.Embedding.create(input = [text], model=model)['data'][0]['embedding']
    
    def get_task_breakup(self, query, func_desc_map):
        func_desc_query = ''
        if len(func_desc_map.keys()):
            for k, v in func_desc_map.items():
                func_desc_query += f"{k} - {v}\n"

            func_desc_query += 'breakdown the following coding task by steps and return the steps. \
                only return the steps, no other text. [ONLY return numbered steps]. use the function and \
                    their descriptions provided here to plan out things so that we can resuse maximum code: \n' + query
        else:
            func_desc_query = 'breakdown the following coding task by steps and return the steps. \
                only return the steps, no other text. [ONLY return numbered steps]: ' + query
        
        context = [
            {"role": "system", "content": "You are AI coding assistant which looks at given list of functions and figures out how to effectively achieve a task"},
            {"role": "user", "content": "create_complex_num: creates a random complex number\n print_complex_num: prints a complex number\n\
                breakdown the coding task by steps and return the steps. \
                only return the steps, no other text. [ONLY return numbered steps]. use the function and \
                    their descriptions provided here to generate tasks. Each task should be self sufficient and well defined: \ngenerate a random complex number and print it "},
            {"role": "assistant", "content": "1. generate a random complex number using the function create_complex_num\n2. print the complex number using the function print_complex_num "},
            {"role": "user", "content": "Above was just an example, now solve the tasks which I will provide further. Reply with 'yes' if you understand"},
            {"role": "assistant", "content": "yes"}
        ]
        task_list = self.get_query(func_desc_query, context)
        task_list = task_list['output'].split('\n')
        return task_list
    
    def generate_task_code(self, task, similar_func_code, class_init_code):
        base_query = 'You are free to choose any logic, code or method the goal is to keep the final code as simple and short as possible.\
              generate the code for the following task (only return the python code). If you have any doubts or are not able to generate\
                  the code return the text "help: [your doubt/issue]":\n' + task
        if similar_func_code:
            query = 'given the following code of similar functions, try to use them directly or modify them: \n'
            for k, v in similar_func_code.items():
                query += 'function: ' + k + '\n'
                query += 'code: ' + v + '\n'

            if class_init_code:
                query += 'following is sample code for how to initialize given classes: \n'
                for k, v in class_init_code.items():
                    query += 'class: ' + k + '\n'
                    query += 'code: ' + v + '\n'
            
            base_query = query + base_query
        
        res = self.get_query(base_query)
        return res['output']
    
    def fix_code_issues(self, final_code):
        code_issues = [
            'unnecessary text in the code',
            'syntax errors in the code',
            'any bugs that you think the code might have'
        ]

        query = 'does this code has any of the following issues. Only respond with yes or no: \n'
        for issue in code_issues:
            query += issue + '\n'

        query += 'code: ' + '\n' + final_code
        res = self.get_query(query)
        print("response of the first check: ", res['output'])
        if res and 'yes' in res['output'].lower():
            query = 'fix the following issues in the given code. If there are no issues with the code then return it as it is: \n'
            for issue in code_issues:
                query += issue + '\n'

            query += 'code: ' + '\n' + final_code
            res = self.get_query(query)
            final_code = res['output']

        # additional fixing
        query = 'this code is not working, fix this code. If everything is fine just return the code as it is. Make any changes that you wish is necessary. ONLY provide the code in the response. No other text: \n'
        query += final_code
        res = self.get_query(query)
        return res['output']
    
    def generate_short_desc(self, function_summary):
        query = 'in two lines or less, generate a short description of the given text:\n' + function_summary
        res = self.get_query(query)
        return res['output']
    
    # given a set of steps and set of functions already present in the code
    # this function determines how to achieve them
    def update_task_list_based_on_function_desc(self, task_list, func_desc_map):
        if not len(func_desc_map.keys()):
            return task_list
        
        func_desc_query = 'these functions are present in the code: \n'
        for k, v in func_desc_map.items():
            func_desc_query += f"{k} - {v}\n"

        base_query = 'which functions given in this prompt can be used for solving this task list. You may also use python in-built functions \
            ONLY return the list function names followed by a single line [SHORT DESCRIPTION] explaining \
                how can the function be used and which steps can be solved. If no function can be used then return NONE: \n'
        for task in task_list:
            base_query += task + '\n'
        
        func_desc_query += base_query
        

        context = [
            {"role": "system", "content": "You are AI coding assistant which looks at given list of functions and figures out which of them can be useful in achieving a set of tasks"},
            {"role": "user", "content": f"these functions are present in the code: \ncreate_complex_num: creates a random complex number\n print_complex_num: prints a complex number\n \
                {base_query} 1. generate a random complex number \n 2. print the square of the complex number"},
            {"role": "assistant", "content": "create_complex_num: this can be used to generate a complex number\nprint_complex_num: this can be used to print a complex number"},
            {"role": "user", "content": f"these functions are present in the code: \ncreate_complex_num: creates a random complex number\n print_complex_num: prints a complex number\n \
                {base_query} create a function to give me weather updates"},
            {"role": "assistant", "content": "NONE"},
            {"role": "user", "content": f"these functions are present in the code: \ncreate_complex_num: creates a random complex number\n print_complex_num: prints a complex number\n \
                {base_query} take two numbers as input. form a complex number using these, first number will be real part, second will be imaginary part. then print that complex number"},
            {"role": "assistant", "content": "print_complex_num: this can be used to print a complex number"},
        ]

        res_task = self.get_query(func_desc_query, context)
        res_task = res_task['output'].split('\n')
        return res_task
    
    def regenerate_task_list(self, combined_task_list, combined_instructions):
        base_query = '\n\nusing the functions provides in this prompt create a new task list. For example if there are \
            10 steps, but they can be solved by a single function "xyz" then return a single step mentioning \
                "use xyz to solve these steps". Find the current steps below, reduce this on the basis of functions provided above: \n'
        opening_instruction = "you are a super efficient coding AI. please understand the use cases of the function below:\n"
        query = opening_instruction + combined_task_list + '\n' + base_query + combined_instructions + '\n'
        context = [
                {"role": "system", "content": "You are AI coding assistant which returns the minimum number of tasks needed to complete a task list when useful functions are given"},
                {"role": "user", "content": opening_instruction + '1. import libraries to get weather data 2.get weather data 3. convert temperature into celcius 4. print temperature' + base_query\
                + 'fetch_weather_data: this provides weather information like temperature, humidity, and pressure'},
                {"role": "assistant", "content": "1. get temperature through fetch_weather_data 2. convert temperature into celcius 3. print temperature"},
                {"role": "user", "content": opening_instruction + '1. import libraries to get weather data 2.get weather data 3. convert temperature into celcius 4. print temperature' + base_query\
                + 'get_temperature: this provides temperature data in celcius'},
                {"role": "assistant", "content": "1. get temperature through get_temperature 2. print temperature"},
            ]
        res = self.get_query(query, context)
        print("\033[1;32mupdated task list:\033[0m Task completed successfully.")
        print('=> Generated task list: \n', res['output'])
        task_list = res['output'].split('\n')

        return task_list
    
    def filter_numbered_list(self, task_list):
        query = 'Below are a list of tasks. Filter out non-empty task and return the list. \
            Also filter out any tasks which require installing/adding new libraries or plugins.\
                  ONLY return the task list and no other accompanying text: \n'
        for task in task_list:
            query += task + '\n'
        
        res = self.get_query(query)
        task_list = res['output'].split('\n')
        return task_list

class TestAIAgent(AIAgent):
    def __init__(self):
        pass

    def is_breakdown_of_task_needed(self, task: str):
        return random.choice(['yes', 'no']) 

    def breakdown_into_subtask(self, task: str):
        return random.choice(['first;second', 'first;second;third']) 

    def solve_task(self, task: str, data=None):
        return 'solved'
    
    def get_function_summary(self, code: str, dict: dict, class_name: str):
        return "does some random stuff"
    
    def get_class_summary(self, class_name, class_code, dict):
        return "does some random class stuff"
    
    def get_text_embedding(self, text):
        return [1] * VECTOR_EMBEDDING_DIM
    
    def get_task_breakup(self, query, func_desc_map):
        return ['code', 'code some more']
    
    def generate_task_code(self, task, similar_func_code, class_init_code):
        return 'some random code'
    
    def generate_short_desc(self, function_summary):
        return 'some random short description'
    
    def fix_code_issues(self, final_code):
        return 'fixed code'
    
    def update_task_list_based_on_function_desc(self, task_list, func_desc_map):
        return task_list
    
    def regenerate_task_list(self, combined_task_list, combined_instructions):
        return combined_task_list.split('\n')
    
    def filter_numbered_list(self, task_list):
        return task_list

def get_ai_agent(debug=False) -> AIAgent:
    if debug:
        return TestAIAgent()
    else:
        return OpenAI()