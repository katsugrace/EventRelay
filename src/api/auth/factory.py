from src.api.auth.base import Auth
from src.api.auth.gitlab_token import GitLabTokenAuth


class AuthFactory:
    AUTHS = {
        'gitlab_token': GitLabTokenAuth
    }

    @classmethod
    def create(cls, name: str, **kwargs) -> Auth:
        if name not in cls.AUTHS:
            raise ValueError(f'Auth "{name}" is not registered')

        return cls.AUTHS[name](**kwargs)
