import re
from src.filters.base import BaseFilter


class EqualsFilter(BaseFilter):
    def __init__(self, field: str, value):
        super().__init__(field)
        self.value = value

    def check(self, data: dict) -> bool:
        return self.get_value(data) == self.value


class NotEqualsFilter(BaseFilter):
    def __init__(self, field: str, value):
        super().__init__(field)
        self.value = value

    def check(self, data: dict) -> bool:
        return self.get_value(data) != self.value


class InFilter(BaseFilter):
    def __init__(self, field: str, values: list):
        super().__init__(field)
        self.values = values

    def check(self, data: dict) -> bool:
        return self.get_value(data) in self.values


class ExistsFilter(BaseFilter):
    def __init__(self, field: str, should_exist: bool):
        super().__init__(field)
        self.should_exist = should_exist

    def check(self, data: dict) -> bool:
        value = self.get_value(data)
        return (value is not None) == self.should_exist


class ContainsFilter(BaseFilter):
    def __init__(self, field: str, value: str):
        super().__init__(field)
        self.value = value

    def check(self, data: dict) -> bool:
        val = self.get_value(data)
        return self.value in val if isinstance(val, str) else False


class RegexFilter(BaseFilter):
    def __init__(self, field: str, pattern: str):
        super().__init__(field)
        self.pattern = re.compile(pattern)

    def check(self, data: dict) -> bool:
        val = self.get_value(data)
        return isinstance(val, str) and bool(self.pattern.search(val))


class GreaterThanFilter(BaseFilter):
    def __init__(self, field: str, value: float):
        super().__init__(field)
        self.value = value

    def check(self, data: dict) -> bool:
        val = self.get_value(data)
        return val > self.value if val is not None else False


class LessThanFilter(BaseFilter):
    def __init__(self, field: str, value: float):
        super().__init__(field)
        self.value = value

    def check(self, data: dict) -> bool:
        return (val := self.get_value(data)) is not None and val < self.value


class StartsWithFilter(BaseFilter):
    def __init__(self, field: str, value: str):
        super().__init__(field)
        self.value = value

    def check(self, data: dict) -> bool:
        val = self.get_value(data)
        return val.startswith(self.value) if isinstance(val, str) else False


class EndsWithFilter(BaseFilter):
    def __init__(self, field: str, value: str):
        super().__init__(field)
        self.value = value

    def check(self, data: dict) -> bool:
        val = self.get_value(data)
        return val.endswith(self.value) if isinstance(val, str) else False


class NotInFilter(BaseFilter):
    def __init__(self, field: str, values: list):
        super().__init__(field)
        self.values = values

    def check(self, data: dict) -> bool:
        return self.get_value(data) not in self.values
