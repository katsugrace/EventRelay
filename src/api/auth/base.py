from abc import ABC, abstractmethod

from fastapi import Request


class Auth(ABC):
    @abstractmethod
    async def validate(self, request: Request):
        raise NotImplementedError
