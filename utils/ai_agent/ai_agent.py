from abc import ABC
import time
import random
from typing import List

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

    def generate_task_code(self, task, similar_func_code):
        pass

    def fix_code_issues(self, final_code):
        pass

    def generate_short_desc(self, function_summary):
        pass

    def update_task_list_based_on_function_desc(self, task_list, function_desc_map):
        pass


class OpenAI(AIAgent):
    def __init__(self):
        import openai

        self.openai = openai
        openai.api_key = OPENAI_API_KEY
        self.ai_model = OpenAIModel.gpt_turbo
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
                "temperature": 0.2  # more focused
            }
    
    def get_query(self, query, context=None):
        data = self._generate_params(query, context)
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
    
    def generate_task_code(self, task, similar_func_code):
        base_query = 'You are free to choose any logic, code or method the goal is to keep the final code as simple and short as possible.\
              generate the code for the following task (only return the python code). If you have any doubts or are not able to generate\
                  the code return the text "help: [your doubt/issue]":\n' + task
        if similar_func_code:
            query = 'given the following code of similar functions, try to use them directly or modify them: \n'
            for k, v in similar_func_code.items():
                query += 'function: ' + k + '\n'
                query += 'code: ' + v + '\n'
            
            base_query = query + base_query
        
        res = self.get_query(base_query)
        return res['output']
    
    def fix_code_issues(self, final_code):
        code_issues = [
            'remove unnecessary text from the code',
            'fix syntax errors in the code',
            'fix any bugs that you think the code might have'
        ]
        query = 'fix the following issues in the given code: \n'
        for issue in code_issues:
            query += issue + '\n'
        query += 'code: ' + '\n' + final_code
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

        base_query = 'which functions given in this prompt can be used for solving this task list. \
            ONLY return the list function names followed by a single line [SHORT DESCRIPTION] explaining how can the function be used.\
                  If no function can be used then return NONE: \n'
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
    
    def generate_task_code(self, task, similar_func_code):
        return 'some random code'
    
    def generate_short_desc(self, function_summary):
        return 'some random short description'
    
    def fix_code_issues(self, final_code):
        return 'fixed code'
    
    def update_task_list_based_on_function_desc(self, task_list, func_desc_map):
        return task_list

def get_ai_agent(debug=False) -> AIAgent:
    if debug:
        return TestAIAgent()
    else:
        return OpenAI()