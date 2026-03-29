import pytest
from src.filters.factory import FilterFactory
from src.filters.engine import TriggerEngine
from src.filters.base import BaseFilter


class DummyTrigger:
    def __init__(self, filters):
        self.filters = filters


@pytest.mark.parametrize(
    'config,data,expected',
    [
        ({'field': 'name', 'equals': 'Alice'}, {'name': 'Alice'}, True),
        ({'field': 'name', 'equals': 'Alice'}, {'name': 'Bob'}, False),

        ({'field': 'name', 'not_equals': 'Alice'}, {'name': 'Bob'}, True),
        ({'field': 'name', 'not_equals': 'Alice'}, {'name': 'Alice'}, False),

        ({'field': 'age', 'gt': 18}, {'age': 20}, True),
        ({'field': 'age', 'gt': 18}, {'age': 17}, False),

        ({'field': 'age', 'lt': 18}, {'age': 17}, True),
        ({'field': 'age', 'lt': 18}, {'age': 20}, False),

        ({'field': 'tags', 'in': ['python', 'pytest']}, {'tags': 'python'}, True),
        ({'field': 'tags', 'in': ['python', 'pytest']}, {'tags': 'java'}, False),

        ({'field': 'email', 'exists': True}, {'email': 'test@test.com'}, True),
        ({'field': 'email', 'exists': True}, {}, False),

        ({'field': 'description', 'contains': 'hello'}, {'description': 'say hello'}, True),
        ({'field': 'description', 'contains': 'hello'}, {'description': 'bye'}, False),

        ({'field': 'username', 'regex': r'^user\d+$'}, {'username': 'user123'}, True),
        ({'field': 'username', 'regex': r'^user\d+$'}, {'username': 'admin'}, False),

        ({'field': 'title', 'startswith': 'Dr.'}, {'title': 'Dr. Smith'}, True),
        ({'field': 'title', 'startswith': 'Dr.'}, {'title': 'Mr. Smith'}, False),

        ({'field': 'title', 'endswith': 'PhD'}, {'title': 'Alice PhD'}, True),
        ({'field': 'title', 'endswith': 'PhD'}, {'title': 'Alice MD'}, False),
    ]
)
def test_filter_factory_check(config, data, expected):
    filt = FilterFactory.create(config)
    assert filt.check(data) == expected


def test_trigger_engine_all_pass():
    configs = [
        {'field': 'name', 'equals': 'Alice'},
        {'field': 'age', 'gt': 18},
        {'field': 'email', 'exists': True},
    ]

    trigger = DummyTrigger(filters=configs)
    engine = TriggerEngine(trigger)
    body = {
        'name': 'Alice',
        'age': 25, 'email':
        'a@example.com'
    }

    assert engine.check(body) is True


def test_trigger_engine_one_fail():
    configs = [
        {'field': 'name', 'equals': 'Alice'},
        {'field': 'age', 'gt': 18},
        {'field': 'email', 'exists': True},
    ]

    trigger = DummyTrigger(filters=configs)
    engine = TriggerEngine(trigger)
    body = {
        'name': 'Alice',
        'age': 17,
        'email': 'a@example.com'
    }

    assert engine.check(body) is False


def test_filter_factory_unknown_config():
    config = {
        'field': 'name',
        'unknown_op': 'value'
    }

    with pytest.raises(ValueError) as exc_info:
        FilterFactory.create(config)

    assert 'Unknown filter config' in str(exc_info.value)


class DummyBaseFilter(BaseFilter):
    def check(self, _: dict) -> bool:
        return super().check(_)


def test_get_value_returns_none_for_non_dict_field():
    bf = DummyBaseFilter('nested.key')
    data = {
        'nested': 'not_a_dict'
    }

    assert bf.get_value(data) is None


def test_get_value_returns_none_for_missing_key():
    bf = DummyBaseFilter('nested.key')
    data = {
        'nested': {}
    }

    assert bf.get_value(data) is None


def test_get_value_returns_value():
    bf = DummyBaseFilter('nested.key')
    data = {
        'nested': {'key': 42}
    }

    assert bf.get_value(data) == 42


def test_check_not_implemented():
    bf = BaseFilter('any_field')
    with pytest.raises(NotImplementedError):
        bf.check({})
