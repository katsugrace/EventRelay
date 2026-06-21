import pytest
from fastapi import HTTPException
from starlette.requests import Request

from src.api.auth.gitlab_token import GitLabTokenAuth


def make_request(headers=None):
    headers = headers or {}

    async def receive():
        return {"type": "http.request"}

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/",
        "headers": [
            (k.lower().encode(), v.encode())
            for k, v in headers.items()
        ],
    }

    return Request(scope, receive)


def test_init_without_token_env():
    with pytest.raises(ValueError, match="GitLabTokenAuth requires token_env"):
        GitLabTokenAuth()


def test_init_reads_token_from_env(monkeypatch):
    monkeypatch.setenv("GITLAB_TOKEN", "secret")

    auth = GitLabTokenAuth(token_env="GITLAB_TOKEN")

    assert auth.token == "secret"


def test_init_uses_token_env_as_fallback(monkeypatch):
    monkeypatch.delenv("DIRECT_TOKEN", raising=False)

    auth = GitLabTokenAuth(token_env="DIRECT_TOKEN")

    assert auth.token == "DIRECT_TOKEN"


@pytest.mark.asyncio
async def test_validate_success(monkeypatch):
    monkeypatch.setenv("GITLAB_TOKEN", "secret")

    auth = GitLabTokenAuth(token_env="GITLAB_TOKEN")

    request = make_request({
        "X-Gitlab-Token": "secret"
    })

    result = await auth.validate(request)

    assert result is None


@pytest.mark.asyncio
async def test_validate_invalid_token(monkeypatch):
    monkeypatch.setenv("GITLAB_TOKEN", "secret")

    auth = GitLabTokenAuth(token_env="GITLAB_TOKEN")

    request = make_request({
        "X-Gitlab-Token": "wrong"
    })

    with pytest.raises(HTTPException) as exc:
        await auth.validate(request)

    assert exc.value.status_code == 403
    assert exc.value.detail == "Invalid GitLab token"


@pytest.mark.asyncio
async def test_validate_missing_header(monkeypatch):
    monkeypatch.setenv("GITLAB_TOKEN", "secret")

    auth = GitLabTokenAuth(token_env="GITLAB_TOKEN")

    request = make_request()

    with pytest.raises(HTTPException) as exc:
        await auth.validate(request)

    assert exc.value.status_code == 403
