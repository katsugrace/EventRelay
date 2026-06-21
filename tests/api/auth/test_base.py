import pytest
from fastapi import Request

from src.api.auth.base import Auth


@pytest.mark.asyncio
async def test_auth_validate_not_implemented():
    class DummyAuth(Auth):
        async def validate(self, request: Request):
            await super().validate(request)

    auth = DummyAuth()
    with pytest.raises(NotImplementedError):
        await auth.validate(None)
