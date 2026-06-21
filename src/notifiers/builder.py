from typing import Dict
from src.notifiers.factory import NotifierFactory
from src.config.models import NotifierConfig


def build_notifiers(
        notifiers_config: Dict[str, NotifierConfig]) -> Dict[str, object]:
    result = {}
    for name, cfg in notifiers_config.items():
        result[name] = NotifierFactory.create(
            cfg.type,
            **cfg.model_dump(exclude={'type'})
        )

    return result
