import httpx
import logging
import asyncio
import json

from typing import Tuple, Optional
from src.notifiers.base import Notifier

logger = logging.getLogger(__name__)


class TelegramNotifier(Notifier):
    def __init__(self, **kwargs):
        token_env = kwargs.get('token_env')
        if not token_env:
            logger.error('TelegramNotifier requires token_env parameter')
            raise ValueError('TelegramNotifier требует token_env')

        import os
        self.token = os.getenv(token_env, token_env)
        if not self.token:
            logger.error(f'Token not found in environment variable: {token_env}')
            raise ValueError(f'Token not found in environment variable: {token_env}')

        self.chat_ids = kwargs.get('chat_ids')
        if not self.chat_ids:
            logger.error('TelegramNotifier requires chat_ids parameter')
            raise ValueError('TelegramNotifier требует chat_ids')

        self.max_retries = kwargs.get('max_retries', 3)
        self.retry_delay = kwargs.get('retry_delay', 1)

        self.base_url = f'https://api.telegram.org/bot{self.token}'

    def _parse_chat_id(self, chat_string: str) -> Optional[Tuple[str, str]]:
        parts = str(chat_string).strip().split('/')
        try:
            chat_id = str(parts[0])
            thread_id = str(parts[1]) if len(parts) > 1 else None
            return chat_id, thread_id
        except (ValueError, IndexError) as e:
            logger.error(f'Invalid chat_id format: {chat_string}')
            raise ValueError(f'Invalid chat_id format: {chat_string}') from e

    async def send(self, message: str) -> None:
        logger.info(f'Sending message to {len(self.chat_ids)} Telegram chat(s)')
        await self._broadcast(message)

    async def skip(self, message: str) -> None:
        logger.debug(f'Skipping notification: {message}')

    async def _broadcast(self, message: str) -> None:
        async with httpx.AsyncClient(timeout=10.0) as client:
            tasks = [
                self._send_to_chat_with_retry(client, chat_entry, message)
                for chat_entry in self.chat_ids
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)
            failed_chats = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    chat_entry = self.chat_ids[i]
                    failed_chats.append(chat_entry)
                    logger.error(f'Failed to send to chat {chat_entry}')

            if failed_chats:
                raise RuntimeError(
                    f'Failed to send message to {len(failed_chats)} chat(s): {failed_chats}'
                )

    async def _send_to_chat_with_retry(
            self,
            client: httpx.AsyncClient,
            chat_entry: str,
            message: str):
        chat_id, thread_id = self._parse_chat_id(chat_entry)
        for attempt in range(1, self.max_retries + 1):
            try:
                response = await self._send_to_chat(client, chat_id, thread_id, message)
                if response['ok']:
                    logger.info(
                        f'Message sent successfully to chat {chat_entry} '
                        f'(message_id: {response.get("result", {}).get("message_id")})'
                    )
                    return

                error_code = response.get('error_code')
                logger.error(
                    f'Telegram API error for chat {chat_entry}: '
                    f'[{error_code}] '
                )

                if error_code in [400, 403, 404]:
                    logger.error(
                        f'Non-retryable error {error_code} for chat {chat_entry}'
                    )
                    raise RuntimeError(
                        f'Telegram API error: [{error_code}]'
                    )

                if attempt == self.max_retries:
                    raise RuntimeError(
                        f'Telegram API error after {self.max_retries} attempts: [{error_code}]'
                    )

                delay = self.retry_delay * (2 ** (attempt - 1))
                logger.warning(
                    f'Telegram API error {error_code} for chat {chat_entry}, '
                    f'retrying in {delay}s (attempt {attempt}/{self.max_retries})'
                )
                await asyncio.sleep(delay)
            except httpx.TimeoutException as e:
                if attempt == self.max_retries:
                    logger.error(
                        f'Timeout sending to chat {chat_entry} '
                        f'after {self.max_retries} attempts: {e}'
                    )
                    raise

                delay = self.retry_delay * (2 ** (attempt - 1))
                logger.warning(
                    f'Timeout sending to chat {chat_entry}, '
                    f'retrying in {delay}s (attempt {attempt}/{self.max_retries})'
                )

                await asyncio.sleep(delay)
            except httpx.RequestError as e:
                if attempt == self.max_retries:
                    logger.error(
                        f'Network error sending to chat {chat_entry} '
                        f'after {self.max_retries} attempts: {e}'
                    )
                    raise

                delay = self.retry_delay * (2 ** (attempt - 1))
                logger.warning(
                    f'Network error sending to chat {chat_entry}, '
                    f'retrying in {delay}s (attempt {attempt}/{self.max_retries}): {e}'
                )
                await asyncio.sleep(delay)
            except Exception as e:
                if attempt == self.max_retries:
                    logger.error(
                        f'Unexpected error sending to chat {chat_entry} '
                        f'after {self.max_retries} attempts: {e}'
                    )
                    raise

                delay = self.retry_delay * (2 ** (attempt - 1))
                logger.warning(
                    f'Unexpected error sending to chat {chat_entry}, '
                    f'retrying in {delay}s (attempt {attempt}/{self.max_retries}): {e}'
                )

                await asyncio.sleep(delay)

    async def _send_to_chat(
            self,
            client: httpx.AsyncClient,
            chat_id: int,
            thread_id: Optional[int],
            message: str) -> dict:
        payload = {
            'chat_id': chat_id,
            'text': message,
        }

        if thread_id is not None:
            payload['message_thread_id'] = thread_id

        resp = await client.post(
            f'{self.base_url}/sendMessage',
            json=payload,
            timeout=10.0
        )

        if resp.status_code != 200:
            logger.error(
                f'Telegram API HTTP error {resp.status_code} for chat {chat_id}: '
                f'{resp.text[:200]}'
            )
            resp.raise_for_status()

        try:
            result = resp.json()
            return result
        except json.JSONDecodeError:
            logger.error('Failed to parse Telegram API response')
            raise RuntimeError('Invalid JSON response from Telegram API')
