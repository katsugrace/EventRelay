import pytest

from src.notifiers.factory import NotifierFactory
from src.notifiers.mock import MockNotifier


def test_notifier_factory_create_and_error():
    n = NotifierFactory.create('mock')
    assert isinstance(n, MockNotifier)
    with pytest.raises(ValueError):
        NotifierFactory.create('unknown')
