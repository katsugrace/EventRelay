from typing import Dict


class BaseFilter:
    def __init__(self, field: str):
        self.field = field

    def get_value(self, data: dict):
        value = data
        for key in self.field.split('.'):
            if not isinstance(value, dict):
                return None
            value = value.get(key)
            if value is None:
                return None

        return value

    def check(self, _: Dict) -> bool:
        raise NotImplementedError
