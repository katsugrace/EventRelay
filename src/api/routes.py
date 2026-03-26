from fastapi import FastAPI
from typing import Dict
from src.config.models import Trigger
from src.filters.engine import TriggerEngine
from pydantic import BaseModel


class EmptyBody(BaseModel):
    pass


def register_routes(app: FastAPI, triggers: Dict[str, Trigger]):
    for name, trigger in triggers.items():
        engine = TriggerEngine(trigger)

        for method in trigger.methods:
            async def _endpoint(body: dict):
                if not engine.check(body):
                    return {'status': 'skipped'}

                return {'status': 'ok'}

            _endpoint.__name__ = f'{name}_{method.lower()}'
            app.add_api_route(
                path=trigger.path,
                endpoint=_endpoint,
                methods=[method],
                tags=trigger.tags or ['Triggers'],
                summary=trigger.name or name,
                description=getattr(trigger, 'description', None)
            )
