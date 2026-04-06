from pydantic import BaseModel, ConfigDict
from typing import List, Dict, Optional


class Filter(BaseModel):
    field: str
    equals: Optional[str] = None


class Message(BaseModel):
    text: str


class AuthConfig(BaseModel):
    type: str
    model_config = ConfigDict(extra='allow')


class NotifierConfig(BaseModel):
    type: str
    model_config = ConfigDict(extra='allow')


class Trigger(BaseModel):
    path: str
    filters: List[Filter]
    message: Message
    notify: List[str]
    name: Optional[str] = None
    methods: Optional[List[str]] = ['POST']
    tags: Optional[List[str]] = None
    active: Optional[bool] = True
    description: Optional[str] = None
    auth: Optional[str] = None


class AppConfig(BaseModel):
    notifiers: Dict[str, NotifierConfig]
    triggers: Dict[str, Trigger]
    auths: Optional[Dict[str, AuthConfig]] = {}
