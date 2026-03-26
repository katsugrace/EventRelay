from fastapi import FastAPI
from src.api.routes import register_routes
from src.config.loader import Config
from src.env import EnvConfig
from src.notifiers.factory import NotifierFactory


app = FastAPI(title='Event Relay API')
env = EnvConfig()
config = Config(path=env.config)
notifier = NotifierFactory.create(name=config.get_notify())

register_routes(
  app=app,
  triggers=config.get_all_triggers(),
  notifier=notifier
)
