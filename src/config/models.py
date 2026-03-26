from pydantic import BaseModel
from typing import List, Dict, Optional


class Filter(BaseModel):
    field: str
    equals: Optional[str] = None


class Message(BaseModel):
    text: str


class TelegramNotify(BaseModel):
    chat_id: int


class Notify(BaseModel):
    telegram: Optional[List[TelegramNotify]] = None


class Trigger(BaseModel):
    path: str
    filters: List[Filter]
    message: Message
    notify: Notify
    name: Optional[str] = None


class AppConfig(BaseModel):
    triggers: Dict[str, Trigger]
