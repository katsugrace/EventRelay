import logging
from typing import List

from src.notifiers.base import Notifier

logger = logging.getLogger(__name__)


class MockNotifier(Notifier):
    def __init__(self):
        self.sent: List[str] = []
        self.skipped: List[str] = []

    async def send(self, message: str) -> None:
        logger.info(f'Simulating send: {message[:50]}...')
        self.sent.append(message)

    async def skip(self, message: str) -> None:
        logger.debug(f'Skipping: {message}')
        self.skipped.append(message)
