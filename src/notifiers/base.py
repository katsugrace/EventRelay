from abc import ABC, abstractmethod


class Notifier(ABC):
    @abstractmethod
    def send(self, message: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def skip(self, message: str) -> None:
        raise NotImplementedError
