from abc import ABC
import time
import random

from settings import FORCE_SUB_TASK_CREATION, OPENAI_API_KEY
from utils.ai_agent.constants import OpenAIModel


class AIAgent(ABC):
    def __init__(self):
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

    def _generate_params(self, prompt):
        return {
                "model": self.ai_model.model,
                "messages": [{"role": "user", "content": prompt}]
            }
    
    def get_query(self, query):
        data = self._generate_params(query)
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
        return [1, 2, 3]

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
        return [1, 2, 3]

def get_ai_agent(debug=False) -> AIAgent:
    if debug:
        return TestAIAgent()
    else:
        return OpenAI()