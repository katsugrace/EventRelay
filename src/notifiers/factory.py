from src.notifiers.base import Notifier
from src.notifiers.mock import MockNotifier
from src.notifiers.telegram import TelegramNotifier


class NotifierFactory:
    NOTIFIERS = {
        'mock': MockNotifier,
        'telegram': TelegramNotifier
    }

    @classmethod
    def create(cls, name: str, **kwargs) -> Notifier:
        if name not in cls.NOTIFIERS:
            raise ValueError(f'Notifier "{name}" is not registered')

        return cls.NOTIFIERS[name](**kwargs)
