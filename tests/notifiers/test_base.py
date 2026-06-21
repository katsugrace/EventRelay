import pytest

from src.notifiers.base import Notifier


@pytest.mark.asyncio
async def test_check_not_implemented():
    class DummyNotifier(Notifier):
        async def send(self, message: str) -> None:
            await super().send(message)

        async def skip(self, message: str) -> None:
            await super().skip(message)

    n = DummyNotifier()
    with pytest.raises(NotImplementedError):
        await n.send('test')

    with pytest.raises(NotImplementedError):
        await n.skip('test')
