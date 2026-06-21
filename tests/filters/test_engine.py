from src.filters.engine import TriggerEngine


def test_trigger_engine_all_filters_true():
    class DummyTrigger:
        filters = [{'field': 'k', 'equals': 'v'}]

    engine = TriggerEngine(DummyTrigger)
    assert engine.check({'k': 'v'})
    assert not engine.check({'k': 'nope'})


def test_trigger_engine_all_pass():
    configs = [
        {'field': 'name', 'equals': 'Alice'},
        {'field': 'age', 'gt': 18},
        {'field': 'email', 'exists': True},
    ]

    class DummyTrigger2:
        def __init__(self, filters):
            self.filters = filters

    trigger = DummyTrigger2(filters=configs)
    engine = TriggerEngine(trigger)
    body = {
        'name': 'Alice',
        'age': 25, 'email': 'a@example.com'
    }

    assert engine.check(body) is True


def test_trigger_engine_one_fail():
    configs = [
        {'field': 'name', 'equals': 'Alice'},
        {'field': 'age', 'gt': 18},
        {'field': 'email', 'exists': True},
    ]

    class DummyTrigger3:
        def __init__(self, filters):
            self.filters = filters

    trigger = DummyTrigger3(filters=configs)
    engine = TriggerEngine(trigger)
    body = {
        'name': 'Alice',
        'age': 17,
        'email': 'a@example.com'
    }

    assert engine.check(body) is False
