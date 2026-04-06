import logging

from src.api.auth.base import Auth
from fastapi import HTTPException, Request

logger = logging.getLogger(__name__)


class GitLabTokenAuth(Auth):
    def __init__(self, **kwargs):
        token_env = kwargs.get('token_env')
        if not token_env:
            logger.error('GitLabTokenAuth requires token_env parameter')
            raise ValueError('GitLabTokenAuth requires token_env')

        import os
        self.token = os.getenv(token_env, token_env)
        if not self.token:
            logger.error(f'Token not found in environment variable: {token_env}')
            raise ValueError(f'Token not found in environment variable: {token_env}')

    async def validate(self, request: Request):
        if request.headers.get('X-Gitlab-Token') != self.token:
            raise HTTPException(status_code=403, detail='Invalid GitLab token')
