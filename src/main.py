from fastapi import FastAPI
from src.api.routes import register_routes
from src.config.loader import Config
from src.env import EnvConfig


app = FastAPI(title='Event Relay API')
env = EnvConfig()
config = Config(env.config)

register_routes(app, config.get_all_triggers())
