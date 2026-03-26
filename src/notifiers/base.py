from abc import ABC, abstractmethod


class Notifier(ABC):
    @abstractmethod
    def send(self, _: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def skip(self, _: str) -> None:
        raise NotImplementedError
