import pytest

from src.config.models import NotifierConfig
from src.notifiers.builder import build_notifiers
from src.notifiers.mock import MockNotifier
from src.notifiers.telegram import TelegramNotifier


def test_build_mock_notifier():
    cfg = {"mock1": NotifierConfig(type="mock")}
    result = build_notifiers(cfg)
    assert "mock1" in result
    assert isinstance(result["mock1"], MockNotifier)


def test_build_unknown_notifier_raises():
    cfg = {"bad": NotifierConfig(type="not_a_real_notifier")}
    with pytest.raises(ValueError):
        build_notifiers(cfg)


def test_build_telegram_notifier_with_params():
    cfg = {"tg": NotifierConfig(type="telegram", token_env="fake_token", chat_ids=["123"])}
    result = build_notifiers(cfg)
    assert "tg" in result
    assert isinstance(result["tg"], TelegramNotifier)
    assert "fake_token" in result["tg"].base_url
