import pytest
from unittest.mock import AsyncMock
from fastapi import FastAPI
from fastapi.testclient import TestClient

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
