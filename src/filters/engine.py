from src.filters.factory import FilterFactory


class TriggerEngine:
    def __init__(self, trigger):
        self.trigger = trigger
        self.filters = FilterFactory.create_many(trigger.filters or [])

    def check(self, body: dict) -> bool:
        return all(f.check(body) for f in self.filters)
