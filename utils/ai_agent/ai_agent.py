from abc import ABC
import time
import random

from settings import OPENAI_API_KEY
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


class OpenAI(AIAgent):
    def __init__(self):
        import openai

        self.openai = openai
        openai.api_key = OPENAI_API_KEY
        self.ai_model = OpenAIModel.gpt_turbo
        self._set_prompts()
    
    def _set_prompts(self):
        self.IS_BREAKDOWN_REQUIRED_PROMPT = "Do this question needs to be broken into sub-tasks or it is trivial. Reply with only yes or no? - "
        self.BREAKDOWN_INTO_SUBTASK = "break this task in 3 or less sub-tasks (separated by ';'):\n"
        self.SOLVE_TASK = "answer this task:\n"

    def _generate_params(self, prompt):
        return {
                "model": self.ai_model.model,
                "messages": [{"role": "user", "content": prompt}]
            }
    
    def get_query(self, query):
        data = self._generate_params(query)
        start_time = time.time()
        try:
            response = self.openai.Completion.create(**data)
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
        query = self.IS_BREAKDOWN_REQUIRED_PROMPT + task
        res = self.get_query(query)
        return res['output']

    def breakdown_into_subtask(self, task: str):
        query = self.BREAKDOWN_INTO_SUBTASK + task
        res = self.get_query(query)
        return res['output']
    
    def solve_task(self, task: str):
        query = self.SOLVE_TASK + task
        res = self.get_query(query)
        return res['output']


class TestAIAgent(AIAgent):
    def __init__(self):
        pass

    def is_breakdown_of_task_needed(self, task: str):
        return random.choice(['yes', 'no']) 

    def breakdown_into_subtask(self, task: str):
        return random.choice(['first;second', 'first;second;third']) 

    def solve_task(self, task: str):
        return 'solved'
    

def get_ai_agent(debug=False) -> AIAgent:
    if debug:
        return TestAIAgent()
    else:
        return OpenAI()