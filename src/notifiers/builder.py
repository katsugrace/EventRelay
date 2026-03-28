from src.notifiers.factory import NotifierFactory
from src.config.models import NotifierConfig
from typing import Dict


def build_notifiers(notifiers_config: Dict[str, NotifierConfig]) -> Dict[str, object]:
    result = {}
    for name, cfg in notifiers_config.items():
        kwargs = {}

        token = cfg.get_token()
        if token:
            kwargs['token'] = token

        if cfg.chat_ids:
            kwargs['chat_ids'] = cfg.chat_ids

        result[name] = NotifierFactory.create(cfg.type, **kwargs)

    return result