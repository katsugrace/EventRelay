import pytest

from src.filters.factory import FilterFactory


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
        ({'field': 'tags', 'in': ['python', 'pytest']}, {'tags': ['java', 'python']}, True),

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


def test_filter_factory_unknown_config():
    config = {
        'field': 'name',
        'unknown_op': 'value'
    }

    import pytest as _pytest
    with _pytest.raises(ValueError) as exc_info:
        FilterFactory.create(config)

    assert 'Unknown filter config' in str(exc_info.value)
