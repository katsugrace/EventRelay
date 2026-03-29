import pytest
from src.env import EnvConfig


@pytest.fixture
def settings_env(monkeypatch):
    monkeypatch.setenv("CONFIG_PATH", "test.yaml")
    monkeypatch.setenv("HOST", "88.44.33.77")
    monkeypatch.setenv("PORT", "9043")
    return EnvConfig(_env_file=None)


def test_env_config(settings_env):
    assert settings_env.config == "test.yaml"
    assert settings_env.host == "88.44.33.77"
    assert settings_env.port == 9043


def test_env_config_defaults(monkeypatch):
    monkeypatch.delenv("CONFIG_PATH", raising=False)
    monkeypatch.delenv("HOST", raising=False)
    monkeypatch.delenv("PORT", raising=False)

    settings = EnvConfig(_env_file=None)
    assert settings.config == "config/triggers.yaml"
    assert settings.host == "127.0.0.1"
    assert settings.port == 8000
