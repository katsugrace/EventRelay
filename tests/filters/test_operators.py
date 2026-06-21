import pytest

from src.filters.operators import (
    EqualsFilter,
    NotEqualsFilter,
    InFilter,
    ExistsFilter,
    ContainsFilter,
    RegexFilter,
    GreaterThanFilter,
    LessThanFilter,
    StartsWithFilter,
    EndsWithFilter,
)


@pytest.mark.parametrize("value,expected", [
    ("a", True),
    ("b", False),
])
def test_equals_not_equals(value, expected):
    f = EqualsFilter('x', 'a')
    ne = NotEqualsFilter('x', 'a')
    assert f.check({'x': value}) == expected
    assert ne.check({'x': value}) == (not expected)


def test_in_filter_with_iterables():
    f = InFilter('x', [1, 2, 3])
    assert f.check({'x': 2})
    assert f.check({'x': [3, 9]})
    assert not f.check({'x': 9})


def test_exists_filter():
    f_true = ExistsFilter('a.b', True)
    f_false = ExistsFilter('a.b', False)
    assert f_true.check({'a': {'b': 1}})
    assert not f_true.check({'a': {}})
    assert f_false.check({'a': {}})


def test_contains_and_regex():
    c = ContainsFilter('msg', 'hello')
    r = RegexFilter('msg', r'^hello.*world$')
    assert c.check({'msg': 'say hello there'})
    assert not c.check({'msg': 123})
    assert r.check({'msg': 'hello brave world'})
    assert not r.check({'msg': 'no match'})


def test_comparison_filters():
    gt = GreaterThanFilter('n', 10)
    lt = LessThanFilter('n', 10)
    assert gt.check({'n': 11})
    assert not gt.check({'n': 9})
    assert lt.check({'n': 9})
    assert not lt.check({'n': 11})


def test_starts_ends_with():
    s = StartsWithFilter('t', 'pre')
    e = EndsWithFilter('t', 'end')
    assert s.check({'t': 'prefix'})
    assert not s.check({'t': 123})
    assert e.check({'t': 'the end'})
