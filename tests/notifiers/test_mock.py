import asyncio

from src.notifiers.mock import MockNotifier


def test_mock_notifier_lists():
    m = MockNotifier()
    asyncio.run(m.send('hello'))
    asyncio.run(m.skip('bye'))
    assert m.sent == ['hello']
    assert m.skipped == ['bye']
