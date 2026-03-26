from typing import Dict


class BaseFilter:
    def __init__(self, field: str):
        self.field = field

    def get_value(self, data: dict):
        keys = self.field.split('.')
        value = data

        for key in keys:
            if not isinstance(value, dict):
                return None
            value = value.get(key)

        return value

    def check(self, _: Dict) -> bool:
        raise NotImplementedError
