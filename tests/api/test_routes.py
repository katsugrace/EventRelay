import pytest
from unittest.mock import AsyncMock
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi import HTTPException
import logging

from src.api.routes import create_endpoint, register_routes
from src.config.models import Trigger, Filter, Message
from src.notifiers.base import Notifier


@pytest.fixture
def mock_notifier():
    notifier = AsyncMock(spec=Notifier)
    notifier.send = AsyncMock()
    notifier.skip = AsyncMock()
    return notifier


@pytest.fixture
def sample_trigger():
    return Trigger(
        path='/webhook/test',
        filters=[Filter(field='type', equals='push')],
        message=Message(text='Event: {type} from {repo}'),
        notify=['mock'],
        name='test_trigger',
        methods=['POST']
    )


@pytest.fixture
def sample_trigger_no_filters():
    return Trigger(
        path='/webhook/always',
        filters=[],
        message=Message(text='Always triggered'),
        notify=['mock'],
        name='always_trigger',
        methods=['POST']
    )


class TestCreateEndpoint:
    @pytest.mark.asyncio
    async def test_endpoint_sends_notification_when_filters_match(
            self, sample_trigger, mock_notifier):
        notifiers = {'mock': mock_notifier}
        endpoint = create_endpoint('test_trigger', sample_trigger, notifiers)
        response = await endpoint({'type': 'push', 'repo': 'my-repo'})
        assert response.status_code == 200
        mock_notifier.send.assert_called_once()
        call_args = mock_notifier.send.call_args
        assert 'Event: push from my-repo' in call_args[1]['message']
        mock_notifier.skip.assert_not_called()

    @pytest.mark.asyncio
    async def test_endpoint_skips_notification_when_filters_dont_match(
            self, sample_trigger, mock_notifier):
        notifiers = {'mock': mock_notifier}
        endpoint = create_endpoint('test_trigger', sample_trigger, notifiers)
        response = await endpoint({'type': 'pr', 'repo': 'my-repo'})
        assert response.status_code == 200
        mock_notifier.skip.assert_called_once()
        mock_notifier.send.assert_not_called()

    @pytest.mark.asyncio
    async def test_endpoint_handles_missing_template_fields(
            self, sample_trigger, mock_notifier):
        notifiers = {'mock': mock_notifier}
        endpoint = create_endpoint('test_trigger', sample_trigger, notifiers)
        response = await endpoint({'type': 'push'})
        assert response.status_code == 400
        mock_notifier.send.assert_not_called()

    @pytest.mark.asyncio
    async def test_endpoint_with_multiple_notifiers(
            self, sample_trigger, mock_notifier):
        mock_notifier2 = AsyncMock(spec=Notifier)
        mock_notifier2.send = AsyncMock()
        sample_trigger.notify = ['mock1', 'mock2']
        notifiers = {
            'mock1': mock_notifier,
            'mock2': mock_notifier2
        }

        endpoint = create_endpoint('test_trigger', sample_trigger, notifiers)
        response = await endpoint({'type': 'push', 'repo': 'my-repo'})
        assert response.status_code == 200
        mock_notifier.send.assert_called_once()
        mock_notifier2.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_endpoint_with_no_filters_always_triggers(
            self, sample_trigger_no_filters, mock_notifier):
        notifiers = {'mock': mock_notifier}
        endpoint = create_endpoint(
            'always_trigger',
            sample_trigger_no_filters,
            notifiers)

        response = await endpoint({'random': 'data'})
        assert response.status_code == 200
        mock_notifier.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_endpoint_isolation_between_triggers(
            self, mock_notifier):
        trigger1 = Trigger(
            path='/webhook/test1',
            filters=[Filter(field='type', equals='push')],
            message=Message(text='Trigger 1'),
            notify=['mock'],
            name='trigger1'
        )

        trigger2 = Trigger(
            path='/webhook/test2',
            filters=[Filter(field='type', equals='pr')],
            message=Message(text='Trigger 2'),
            notify=['mock'],
            name='trigger2'
        )

        notifiers = {'mock': mock_notifier}
        endpoint1 = create_endpoint('trigger1', trigger1, notifiers)
        endpoint2 = create_endpoint('trigger2', trigger2, notifiers)
        mock_notifier.reset_mock()
        await endpoint1({'type': 'push'})
        assert mock_notifier.send.call_count == 1
        mock_notifier.reset_mock()
        await endpoint2({'type': 'pr'})
        assert mock_notifier.send.call_count == 1


class TestRegisterRoutes:
    def test_register_routes_creates_endpoints(
            self,
            sample_trigger,
            mock_notifier):
        app = FastAPI()
        triggers = {'test_trigger': sample_trigger}
        notifiers = {'mock': mock_notifier}
        register_routes(app, triggers, notifiers)
        routes = [route.path for route in app.routes]
        assert '/webhook/test' in routes

    def test_register_routes_with_multiple_triggers(self, mock_notifier):
        app = FastAPI()
        triggers = {
            'trigger1': Trigger(
                path='/webhook/1',
                filters=[],
                message=Message(text='T1'),
                notify=['mock']
            ),
            'trigger2': Trigger(
                path='/webhook/2',
                filters=[],
                message=Message(text='T2'),
                notify=['mock']
            ),
        }

        notifiers = {'mock': mock_notifier}
        register_routes(app, triggers, notifiers)
        routes = [route.path for route in app.routes]
        assert '/webhook/1' in routes
        assert '/webhook/2' in routes

    def test_register_routes_with_multiple_methods(self, mock_notifier):
        app = FastAPI()
        trigger = Trigger(
            path='/webhook/test',
            filters=[],
            message=Message(text='Test'),
            notify=['mock'],
            methods=['POST', 'PUT']
        )

        triggers = {'test': trigger}
        notifiers = {'mock': mock_notifier}
        register_routes(app, triggers, notifiers)
        webhook_routes = [
            route for route in app.routes
            if hasattr(route, 'path') and route.path == '/webhook/test'
        ]

        assert len(webhook_routes) > 0, 'No routes found for /webhook/test'
        all_methods = set()
        for route in webhook_routes:
            if hasattr(route, 'methods'):
                all_methods.update(route.methods)
        assert 'POST' in all_methods, \
            f'POST not found. Available: {all_methods}'
        assert 'PUT' in all_methods, \
            f'PUT not found. Available: {all_methods}'

    def test_register_routes_http_methods_with_testclient(self, mock_notifier):
        app = FastAPI()
        trigger = Trigger(
            path='/webhook/test',
            filters=[],
            message=Message(text='Test: {method}'),
            notify=['mock'],
            methods=['POST', 'PUT']
        )

        triggers = {'test': trigger}
        notifiers = {'mock': mock_notifier}
        register_routes(app, triggers, notifiers)
        client = TestClient(app)
        mock_notifier.reset_mock()
        response_post = client.post('/webhook/test', json={'method': 'post'})
        assert response_post.status_code == 200
        mock_notifier.send.assert_called_once()
        mock_notifier.reset_mock()
        response_put = client.put('/webhook/test', json={'method': 'put'})
        assert response_put.status_code == 200
        mock_notifier.send.assert_called_once()


class TestEndToEndWithClient:
    def test_webhook_endpoint_returns_200(self, sample_trigger, mock_notifier):
        app = FastAPI()
        triggers = {'test': sample_trigger}
        notifiers = {'mock': mock_notifier}
        register_routes(app, triggers, notifiers)
        client = TestClient(app)
        response = client.post(
            '/webhook/test',
            json={'type': 'push', 'repo': 'my-repo'}
        )

        assert response.status_code == 200

    def test_webhook_endpoint_with_invalid_filter(
            self, sample_trigger, mock_notifier):
        app = FastAPI()
        triggers = {'test': sample_trigger}
        notifiers = {'mock': mock_notifier}
        register_routes(app, triggers, notifiers)
        client = TestClient(app)
        response = client.post(
            '/webhook/test',
            json={'type': 'pr', 'repo': 'my-repo'}
        )

        assert response.status_code == 200

    def test_multiple_webhooks_independent(self, mock_notifier):
        app = FastAPI()
        triggers = {
            'trigger1': Trigger(
                path='/webhook/1',
                filters=[Filter(field='type', equals='push')],
                message=Message(text='T1: {type}'),
                notify=['mock']
            ),
            'trigger2': Trigger(
                path='/webhook/2',
                filters=[Filter(field='type', equals='pr')],
                message=Message(text='T2: {type}'),
                notify=['mock']
            ),
        }

        notifiers = {'mock': mock_notifier}
        register_routes(app, triggers, notifiers)
        client = TestClient(app)
        mock_notifier.reset_mock()
        response1 = client.post(
            '/webhook/1',
            json={'type': 'push'}
        )

        assert response1.status_code == 200
        mock_notifier.reset_mock()
        response2 = client.post(
            '/webhook/2',
            json={'type': 'pr'}
        )

        assert response2.status_code == 200


@pytest.mark.asyncio
async def test_auth_http_exception_returns_status():
    mock_auth = AsyncMock()
    mock_auth.validate = AsyncMock(side_effect=HTTPException(status_code=401, detail='unauth'))

    trigger = Trigger(
        path='/webhook/auth',
        filters=[],
        message=Message(text='Hi'),
        notify=['mock'],
        auth='a'
    )

    notifiers = {'mock': AsyncMock()}
    endpoint = create_endpoint('t', trigger, notifiers, auths={'a': mock_auth})

    resp = await endpoint({'any': 'data'})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_auth_generic_exception_returns_500():
    mock_auth = AsyncMock()
    mock_auth.validate = AsyncMock(side_effect=Exception('boom'))

    trigger = Trigger(
        path='/webhook/auth2',
        filters=[],
        message=Message(text='Hi'),
        notify=['mock'],
        auth='a'
    )

    notifiers = {'mock': AsyncMock()}
    endpoint = create_endpoint('t2', trigger, notifiers, auths={'a': mock_auth})

    resp = await endpoint({'any': 'data'})
    assert resp.status_code == 500


@pytest.mark.asyncio
async def test_notifier_not_found_returns_207():
    trigger = Trigger(
        path='/webhook/miss',
        filters=[],
        message=Message(text='Hi'),
        notify=['missing']
    )

    endpoint = create_endpoint('miss', trigger, notifiers={})
    resp = await endpoint({'any': 'data'})
    assert resp.status_code == 207
    assert 'errors' in resp.body.decode() or 'errors' in resp.render().body.decode()


@pytest.mark.asyncio
async def test_notifier_send_exception_returns_207():
    sample_trigger = Trigger(
        path='/webhook/test',
        filters=[Filter(field='type', equals='push')],
        message=Message(text='Event: {type}'),
        notify=['mock']
    )
    mock_notifier = AsyncMock()
    mock_notifier.send = AsyncMock(side_effect=Exception('send fail'))
    endpoint = create_endpoint('test_trigger', sample_trigger, {'mock': mock_notifier})
    resp = await endpoint({'type': 'push', 'repo': 'r'})
    assert resp.status_code == 207


def test_register_routes_no_triggers_and_missing_path():
    app = FastAPI()
    mock_notifier = AsyncMock()
    register_routes(app, {}, {'mock': mock_notifier})

    t = Trigger(path='', filters=[], message=Message(text='T'), notify=['mock'])
    register_routes(app, {'t': t}, {'mock': mock_notifier})


def test_register_routes_when_no_notifiers(caplog, mock_notifier):
    app = FastAPI()
    trig = Trigger(path='/webhook/nonotify', filters=[], message=Message(text='T'), notify=[])
    with caplog.at_level(logging.WARNING):
        register_routes(app, {'t': trig}, {'mock': mock_notifier})

    assert any('has no notifiers' in r.message for r in caplog.records)

    routes = [route.path for route in app.routes]
    assert '/webhook/nonotify' in routes


@pytest.mark.asyncio
async def test_skip_notifier_exception_logged():
    trig = Trigger(
        path='/webhook/skip',
        filters=[Filter(field='type', equals='push')],
        message=Message(text='T'),
        notify=['mock']
    )

    mock_notifier = AsyncMock()

    async def raise_skip(message):
        raise Exception('skip fail')

    mock_notifier.skip = AsyncMock(side_effect=raise_skip)
    endpoint = create_endpoint('skip', trig, {'mock': mock_notifier})
    resp = await endpoint({'type': 'other'})
    assert resp.status_code == 200


def test_register_routes_handles_add_api_route_error():
    class BadApp:
        def __init__(self):
            self.routes = []

        def add_api_route(self, *args, **kwargs):
            raise Exception('boom')

    app = BadApp()
    trig = Trigger(path='/p', filters=[], message=Message(text='T'), notify=['mock'])
    register_routes(app, {'t': trig}, {'mock': AsyncMock()})


@pytest.mark.asyncio
async def test_message_format_generic_exception():
    class BadFormat:
        def format(self, **kwargs):
            raise Exception('format error')

    trig = Trigger(path='/m', filters=[], message=Message(text='T'), notify=['mock'])
    trig.message.text = BadFormat()
    endpoint = create_endpoint('m', trig, {'mock': AsyncMock()})

    resp = await endpoint({'a': 1})
    assert resp.status_code == 400
