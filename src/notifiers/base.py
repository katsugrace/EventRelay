from abc import ABC, abstractmethod


class Notifier(ABC):
    @abstractmethod
    async def send(self, message: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def skip(self, message: str) -> None:
        raise NotImplementedError
