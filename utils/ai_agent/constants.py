from dataclasses import dataclass

@dataclass
class BaseModel:
    model: str
    max_tokens: int

@dataclass
class OpenAIModel:
    gpt_turbo = BaseModel("gpt-3.5-turbo", 2000)