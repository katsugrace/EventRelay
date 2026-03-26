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
  EndsWithFilter
)


class FilterFactory:
    OPERATORS = {
        'equals': lambda f, v: EqualsFilter(f, v),
        'not_equals': lambda f, v: NotEqualsFilter(f, v),
        'in': lambda f, v: InFilter(f, v),
        'exists': lambda f, v: ExistsFilter(f, v),
        'contains': lambda f, v: ContainsFilter(f, v),
        'regex': lambda f, v: RegexFilter(f, v),
        'gt': lambda f, v: GreaterThanFilter(f, v),
        'lt': lambda f, v: LessThanFilter(f, v),
        'startswith': lambda f, v: StartsWithFilter(f, v),
        'endswith': lambda f, v: EndsWithFilter(f, v),
    }

    @classmethod
    def create(cls, config):
        if hasattr(config, 'model_dump'):
            data = config.model_dump(by_alias=True, exclude_none=True)
        else:
            data = {k: v for k, v in config.items() if v is not None}

        field = data.get('field')
        for op, builder in cls.OPERATORS.items():
            if op in data:
                return builder(field, data[op])

        raise ValueError(f'Unknown filter config: {config}')

    @classmethod
    def create_many(cls, configs):
        return [cls.create(cfg) for cfg in configs]
