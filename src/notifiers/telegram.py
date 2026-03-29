import httpx
import logging
from src.notifiers.base import Notifier

logger = logging.getLogger(__name__)


class TelegramNotifier(Notifier):
    def __init__(self, **kwargs):
        token_env = kwargs.get('token_env')
        if not token_env:
            raise ValueError('TelegramNotifier требует token_env')

        import os
        self.token = os.getenv(token_env, token_env)
        self.chat_ids = kwargs.get('chat_ids')
        if not self.chat_ids:
            raise ValueError('TelegramNotifier требует chat_ids')

        self.base_url = f'https://api.telegram.org/bot{self.token}'

    async def send(self, message: str) -> None:
        await self._broadcast(message)

    async def skip(self, message: str) -> None:
        logger.debug(f'TelegramNotifier skip message: {message}')

    async def _broadcast(self, message: str) -> None:
        async with httpx.AsyncClient(timeout=5.0) as client:
            tasks = [
                self._send_to_chat(client, chat_id, message)
                for chat_id in self.chat_ids
            ]
            await self._gather(tasks)

    async def _send_to_chat(
            self,
            client: httpx.AsyncClient,
            chat_id: int,
            message: str):
        try:
            resp = await client.post(
                f'{self.base_url}/sendMessage',
                json={
                    'chat_id': chat_id,
                    'text': message
                },
            )
            resp.raise_for_status()
        except Exception as e:
            print(f'An error occurred while sending a messag. Error: {e}')

    async def _gather(self, tasks):
        import asyncio
        await asyncio.gather(*tasks, return_exceptions=True)
