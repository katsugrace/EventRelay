from src.filters.base import BaseFilter


def test_get_value_nested_and_missing():
    b = BaseFilter('a.b.c')
    assert b.get_value({'a': {'b': {'c': 5}}}) == 5
    assert b.get_value({'a': {'b': {}}}) is None
    assert BaseFilter('x').get_value({'x': 1}) == 1


def test_get_value_returns_none_for_non_dict_field():
    bf = BaseFilter('nested.key')
    data = {
        'nested': 'not_a_dict'
    }

    assert bf.get_value(data) is None


def test_get_value_returns_none_for_missing_key():
    bf = BaseFilter('nested.key')
    data = {
        'nested': {}
    }

    assert bf.get_value(data) is None


def test_get_value_returns_value():
    bf = BaseFilter('nested.key')
    data = {
        'nested': {'key': 42}
    }

    assert bf.get_value(data) == 42


def test_check_not_implemented():
    bf = BaseFilter('any_field')
    import pytest as _pytest2
    with _pytest2.raises(NotImplementedError):
        bf.check({})
