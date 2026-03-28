from pydantic import BaseModel
from typing import List, Dict, Optional
import os


class Filter(BaseModel):
    field: str
    equals: Optional[str] = None


class Message(BaseModel):
    text: str


class NotifierConfig(BaseModel):
    type: str
    token_env: Optional[str] = None
    chat_ids: Optional[List[int]] = None

    def get_token(self):
        if self.token_env:
            token = os.getenv(self.token_env)
            if not token:
                raise ValueError(f'ENV variable "{self.token_env}" is not set')
            return token
        return None


class Trigger(BaseModel):
    path: str
    filters: List[Filter]
    message: Message
    notify: List[str]
    name: Optional[str] = None
    methods: Optional[List[str]] = ['POST']
    tags: Optional[List[str]] = None


class AppConfig(BaseModel):
    notifiers: Dict[str, NotifierConfig]
    triggers: Dict[str, Trigger]
