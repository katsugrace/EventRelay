from src.notifiers.base import Notifier
from typing import List


class MockNotifier(Notifier):
    def __init__(self):
        self.sent: List[str] = []
        self.skipped: List[str] = []

    async def send(self, message: str) -> None:
        print(f'[MockNotifier] send: {message}')
        self.sent.append(message)

    async def skip(self, message: str) -> None:
        print(f'[MockNotifier] skip: {message}')
        self.skipped.append(message)
