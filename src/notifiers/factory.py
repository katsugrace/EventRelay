from src.notifiers.base import Notifier
from src.notifiers.mock import MockNotifier


class NotifierFactory:
    NOTIFIERS = {
        'mock': MockNotifier
    }

    @classmethod
    def create(cls, name: str) -> Notifier:
        if name not in cls.NOTIFIERS:
            raise ValueError(f'Filter operator "{name}" is not registered')

        return cls.NOTIFIERS[name]()
