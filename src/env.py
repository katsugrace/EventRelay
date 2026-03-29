from pydantic_settings import BaseSettings
from pydantic import Field


class EnvConfig(BaseSettings):
    config: str = Field('config/triggers.yaml', validation_alias='CONFIG_PATH')
    host: str = Field('127.0.0.1', validation_alias='HOST')
    port: int = Field(8000, validation_alias='PORT')

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "allow",
    }
