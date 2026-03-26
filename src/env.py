from pydantic_settings import BaseSettings
from pydantic import Field


class EnvConfig(BaseSettings):
    config: str = Field('config/triggers.yaml', env='CONFIG_PATH')
    host: str = Field('127.0.0.1', env='HOST')
    port: int = Field(8000, env='PORT')

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        extra = 'allow'
