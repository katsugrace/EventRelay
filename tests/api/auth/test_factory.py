import pytest

from src.api.auth.factory import AuthFactory
from src.api.auth.builder import build_auths
from src.config.models import AuthConfig


def test_auth_factory_and_builder():
    with pytest.raises(ValueError):
        AuthFactory.create('unknown')

    cfg = {'auth1': AuthConfig(type='gitlab_token', token_env='tok')}
    auths = build_auths(cfg)
    assert 'auth1' in auths
