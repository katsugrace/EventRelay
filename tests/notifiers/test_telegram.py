import asyncio
import json
import pytest
import httpx

from src.notifiers.telegram import TelegramNotifier


def test_constructor_missing_params():
    with pytest.raises(ValueError):
        TelegramNotifier()

    with pytest.raises(ValueError):
        TelegramNotifier(token_env='tok')


@pytest.mark.asyncio
async def test_broadcast_raises_when_one_task_fails(monkeypatch):
    t = TelegramNotifier(token_env='tok', chat_ids=['1', '2'])

    async def fake_send(client, chat_entry, message):
        if chat_entry == '1':
            raise Exception('boom')
        return None

    monkeypatch.setattr(t, '_send_to_chat_with_retry', fake_send)
    with pytest.raises(RuntimeError):
        await t._broadcast('hello')


@pytest.mark.asyncio
async def test_send_to_chat_http_and_json_errors():
    t = TelegramNotifier(token_env='tok', chat_ids=['1'])

    class DummyRespError:
        status_code = 500
        text = 'server error'

        def raise_for_status(self):
            raise httpx.HTTPStatusError('err', request=None, response=None)

        def json(self):
            return {}

    class DummyClientError:
        async def post(self, *args, **kwargs):
            return DummyRespError()

    with pytest.raises(httpx.HTTPStatusError):
        await t._send_to_chat(DummyClientError(), '1', None, 'm')

    class DummyRespBadJson:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            raise json.JSONDecodeError('msg', doc='', pos=0)

    class DummyClientBadJson:
        async def post(self, *args, **kwargs):
            return DummyRespBadJson()

    with pytest.raises(RuntimeError):
        await t._send_to_chat(DummyClientBadJson(), '1', None, 'm')


@pytest.mark.asyncio
async def test_send_to_chat_payload_includes_thread():
    t = TelegramNotifier(token_env='tok', chat_ids=['1'])

    class DummyRespOk:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return {'ok': True, 'result': {'message_id': 1}}

    class CapturingClient:
        def __init__(self):
            self.last_payload = None

        async def post(self, url, json=None, timeout=None):
            self.last_payload = json
            return DummyRespOk()

    c = CapturingClient()
    await t._send_to_chat(c, '12', '34', 'hello')
    assert 'message_thread_id' in c.last_payload and c.last_payload['message_thread_id'] == '34'


def test_constructor_token_env_empty(monkeypatch):
    monkeypatch.setenv('EMPTY_TOKEN', '')
    with pytest.raises(ValueError):
        TelegramNotifier(token_env='EMPTY_TOKEN', chat_ids=['1'])


@pytest.mark.asyncio
async def test_send_to_chat_with_retry_non_retriable_after_retries(monkeypatch):
    t = TelegramNotifier(token_env='tok', chat_ids=['1'], max_retries=1, retry_delay=0)

    async def fake_send(client, chat_id, thread_id, message):
        return {'ok': False, 'error_code': 500}

    monkeypatch.setattr(t, '_send_to_chat', fake_send)
    with pytest.raises(RuntimeError):
        await t._send_to_chat_with_retry(object(), '1', 'm')


@pytest.mark.asyncio
async def test_send_to_chat_request_and_generic_exceptions(monkeypatch):
    import httpx as _httpx
    t = TelegramNotifier(token_env='tok', chat_ids=['1'], max_retries=1, retry_delay=0)

    async def raise_request(client, chat_id, thread_id, message):
        raise _httpx.RequestError('net')

    monkeypatch.setattr(t, '_send_to_chat', raise_request)
    with pytest.raises(_httpx.RequestError):
        await t._send_to_chat_with_retry(object(), '1', 'm')

    async def raise_generic(client, chat_id, thread_id, message):
        raise Exception('boom')

    monkeypatch.setattr(t, '_send_to_chat', raise_generic)
    with pytest.raises(Exception):
        await t._send_to_chat_with_retry(object(), '1', 'm')


@pytest.mark.asyncio
async def test_send_to_chat_retry_then_success(monkeypatch):
    t = TelegramNotifier(token_env='tok', chat_ids=['1'], max_retries=2, retry_delay=0)

    responses = [
        {'ok': False, 'error_code': 500},
        {'ok': True, 'result': {'message_id': 99}}
    ]

    async def seq_send(client, chat_id, thread_id, message):
        return responses.pop(0)

    monkeypatch.setattr(t, '_send_to_chat', seq_send)

    async def _noop_sleep(*args, **kwargs):
        return None

    monkeypatch.setattr(asyncio, 'sleep', _noop_sleep)
    await t._send_to_chat_with_retry(object(), '1', 'm')


class DummyResponse:
    def __init__(self, status_code=200, json_data=None, text=''):
        self.status_code = status_code
        self._json_data = json_data
        self.text = text

    def raise_for_status(self):
        if self.status_code != 200:
            raise RuntimeError(f'status {self.status_code}')

    def json(self):
        if isinstance(self._json_data, Exception):
            raise self._json_data
        return self._json_data


class DummyClient:
    def __init__(self, response: DummyResponse):
        self._response = response

    async def post(self, *args, **kwargs):
        return self._response


@pytest.mark.asyncio
async def test_send_to_chat_success(monkeypatch):
    monkeypatch.setenv('TG_TOKEN', 'abc')
    notifier = TelegramNotifier(token_env='TG_TOKEN', chat_ids=['1'])

    resp = DummyResponse(200, {'ok': True, 'result': {'message_id': 1}})
    client = DummyClient(resp)

    result = await notifier._send_to_chat(client, '1', None, 'hello')
    assert result['ok'] is True


@pytest.mark.asyncio
async def test_send_to_chat_http_error_raises(monkeypatch):
    monkeypatch.setenv('TG_TOKEN', 'abc')
    notifier = TelegramNotifier(token_env='TG_TOKEN', chat_ids=['1'])

    resp = DummyResponse(500, json_data={"ok": False}, text='server error')
    client = DummyClient(resp)

    with pytest.raises(RuntimeError):
        await notifier._send_to_chat(client, '1', None, 'hi')


@pytest.mark.asyncio
async def test_send_to_chat_invalid_json_raises(monkeypatch):
    monkeypatch.setenv('TG_TOKEN', 'abc')
    notifier = TelegramNotifier(token_env='TG_TOKEN', chat_ids=['1'])

    decode_err = json.JSONDecodeError('msg', 'doc', 0)
    resp = DummyResponse(200, json_data=decode_err)
    client = DummyClient(resp)

    with pytest.raises(RuntimeError):
        await notifier._send_to_chat(client, '1', None, 'hi')


@pytest.mark.asyncio
async def test_send_to_chat_with_retry_non_retryable(monkeypatch):
    monkeypatch.setenv('TG_TOKEN', 'abc')
    notifier = TelegramNotifier(token_env='TG_TOKEN', chat_ids=['1'], max_retries=3, retry_delay=0)

    async def fake_send_to_chat(client, chat_id, thread_id, message):
        return {'ok': False, 'error_code': 400}

    monkeypatch.setattr(notifier, '_send_to_chat', fake_send_to_chat)
    monkeypatch.setattr(asyncio, 'sleep', lambda *_: asyncio.sleep(0))

    with pytest.raises(RuntimeError):
        await notifier._send_to_chat_with_retry(object(), '1', 'hi')


@pytest.mark.asyncio
async def test_send_to_chat_with_retry_exhausts_on_server_error(monkeypatch):
    monkeypatch.setenv('TG_TOKEN', 'abc')
    notifier = TelegramNotifier(token_env='TG_TOKEN', chat_ids=['1'], max_retries=2, retry_delay=0)

    async def fake_send_to_chat(client, chat_id, thread_id, message):
        return {'ok': False, 'error_code': 500}

    monkeypatch.setattr(notifier, '_send_to_chat', fake_send_to_chat)

    async def _noop_sleep(_):
        return None

    monkeypatch.setattr(asyncio, 'sleep', _noop_sleep)

    with pytest.raises(RuntimeError):
        await notifier._send_to_chat_with_retry(object(), '1', 'hi')


@pytest.mark.asyncio
async def test_send_to_chat_with_retry_handles_timeout_and_request_errors(monkeypatch):
    monkeypatch.setenv('TG_TOKEN', 'abc')
    notifier = TelegramNotifier(token_env='TG_TOKEN', chat_ids=['1'], max_retries=2, retry_delay=0)

    async def fake_send_timeout(client, chat_id, thread_id, message):
        raise httpx.TimeoutException('timeout')

    monkeypatch.setattr(notifier, '_send_to_chat', fake_send_timeout)

    async def _noop_sleep(_):
        return None

    monkeypatch.setattr(asyncio, 'sleep', _noop_sleep)

    with pytest.raises(httpx.TimeoutException):
        await notifier._send_to_chat_with_retry(object(), '1', 'hi')


@pytest.mark.asyncio
async def test_parse_chat_id_raises_on_bad_str(monkeypatch):
    monkeypatch.setenv('TG_TOKEN', 'abc')
    notifier = TelegramNotifier(token_env='TG_TOKEN', chat_ids=['1'])

    class Bad:
        def __str__(self):
            raise ValueError('bad')

    with pytest.raises(ValueError):
        notifier._parse_chat_id(Bad())


@pytest.mark.asyncio
async def test_send_and_skip_call(monkeypatch):
    monkeypatch.setenv('TG_TOKEN', 'abc')
    notifier = TelegramNotifier(token_env='TG_TOKEN', chat_ids=['1'])

    called = {'b': False}

    async def fake_broadcast(msg):
        called['b'] = True

    monkeypatch.setattr(notifier, '_broadcast', fake_broadcast)

    await notifier.send('hello')
    assert called['b']

    await notifier.skip('skip me')


@pytest.mark.asyncio
async def test_send_to_chat_with_retry_handles_request_error(monkeypatch):
    monkeypatch.setenv('TG_TOKEN', 'abc')
    notifier = TelegramNotifier(token_env='TG_TOKEN', chat_ids=['1'], max_retries=2, retry_delay=0)

    async def fake_send_request_error(client, chat_id, thread_id, message):
        raise httpx.RequestError('network')

    monkeypatch.setattr(notifier, '_send_to_chat', fake_send_request_error)

    async def _noop_sleep(_):
        return None

    monkeypatch.setattr(asyncio, 'sleep', _noop_sleep)

    with pytest.raises(httpx.RequestError):
        await notifier._send_to_chat_with_retry(object(), '1', 'hi')
