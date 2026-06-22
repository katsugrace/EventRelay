from typing import Dict

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse

from src.config.models import Trigger
from src.notifiers.base import Notifier
from src.api.auth.base import Auth


def register_status_routes(
        app: FastAPI,
        triggers: Dict[str, Trigger],
        notifiers: Dict[str, Notifier],
        auths: Dict[str, Auth] = {}) -> None:
    async def _status() -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                'status': 'ok',
                'triggers_count': len(triggers) if triggers is not None else 0,
                'notifiers_count': len(notifiers) if notifiers is not None else 0,
                'auths': len(auths) if auths is not None else 0
            }
        )

    app.add_api_route(path='/status', endpoint=_status, methods=['GET'], tags=['Status'])
