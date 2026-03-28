from fastapi import FastAPI
from dotenv import load_dotenv
from src.config.loader import Config
from src.env import EnvConfig
from src.api.routes import register_routes
from src.notifiers.builder import build_notifiers

load_dotenv()

app = FastAPI(title='Event Relay API')
env = EnvConfig()
config = Config(path=env.config)
notifiers = build_notifiers(config.get_notifiers())

register_routes(
    app=app,
    triggers=config.get_all_triggers(),
    notifiers=notifiers
)
