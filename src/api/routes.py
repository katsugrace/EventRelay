from fastapi import FastAPI, Response, status
from typing import Dict
from src.config.models import Trigger
from src.filters.engine import TriggerEngine
from src.notifiers.base import Notifier


def register_routes(
        app: FastAPI,
        triggers: Dict[str, Trigger],
        notifier: Notifier):
    for name, trigger in triggers.items():
        engine = TriggerEngine(trigger)

        for method in trigger.methods:
            async def _endpoint(body: Dict):
                if not engine.check(body):
                    notifier.skip(message=f'Trigger {name} skipped')
                    return Response(status_code=status.HTTP_204_NO_CONTENT)

                notifier.send(message=f'Trigger {name} fired')
                return Response(status_code=status.HTTP_204_NO_CONTENT)

            _endpoint.__name__ = f'{name}_{method.lower()}'
            app.add_api_route(
                path=trigger.path,
                endpoint=_endpoint,
                methods=[method],
                tags=trigger.tags or ['Triggers'],
                summary=trigger.name or name,
                description=getattr(trigger, 'description', None)
            )
