from typing import Dict
from src.api.auth.factory import AuthFactory
from src.config.models import AuthConfig


def build_auths(
        auths_config: Dict[str, AuthConfig]) -> Dict[str, object]:
    result = {}
    for name, cfg in auths_config.items():
        result[name] = AuthFactory.create(
            cfg.type,
            **cfg.model_dump(exclude={'type'})
        )

    return result
