import asyncio
import logging
from typing import Any, Dict, Optional, Callable, Awaitable

from fastapi import FastAPI, Response, Request, HTTPException, status
from fastapi.responses import JSONResponse

from src.config.models import Trigger
from src.filters.engine import TriggerEngine
from src.notifiers.base import Notifier
from src.api.auth.base import Auth

logger = logging.getLogger(__name__)


def create_endpoint(
    trigger_name: str,
    trigger: Trigger,
    notifiers: Dict[str, Notifier],
    auths: Optional[Dict[str, Auth]] = None
) -> Callable[[Dict[str, Any], Optional[Request]], Awaitable[JSONResponse]]:
    """Create an asynchronous FastAPI endpoint handler for a given trigger.

    This function generates and returns an async endpoint function that
    processes incoming events for the specified trigger, performing authentication,
    condition checks, message formatting, and notifications.

    Args:
        trigger_name (str): Identifier for the trigger, used in logging and route naming.
        trigger (Trigger): Configuration object defining trigger conditions, message, path, and notifiers.
        notifiers (Dict[str, Notifier]): Mapping of notifier names to Notifier instances for sending notifications.
        auths (Optional[Dict[str, Auth]]): Mapping of authentication scheme names to Auth handlers.
            If provided and contains the trigger's auth key, the endpoint will perform authentication.

    Returns:
        Callable[[Dict[str, Any], Optional[Request]], Awaitable[JSONResponse]]: An async function
            that handles incoming trigger events and returns a JSONResponse.
    """
    engine = TriggerEngine(trigger)

    async def _endpoint(body: Dict[str, Any], request: Any = None) -> Response:
        """Handle an incoming event for the trigger.

        Validates authentication (if configured), checks trigger conditions, formats the message,
        and sends notifications via configured notifiers.

        Args:
            body (Dict[str, Any]): The JSON payload of the incoming request.
            request (Optional[Request]): The FastAPI Request object, used for authentication.

        Returns:
            JSONResponse: Response indicating success, skip, or error status.
        """
        try:
            if auths and trigger.auth in auths:
                auth_handler = auths[trigger.auth]
                await auth_handler.validate(request)

            logger.info(f'Received event for trigger "{trigger_name}"', extra={'trigger': trigger_name})

            if not engine.check(body):
                logger.debug(
                    f'Trigger "{trigger_name}" conditions not met, skipping',
                    extra={'trigger': trigger_name}
                )

                skip_tasks = []
                skip_names = []
                for notifier_name in trigger.notify:
                    if notifier_name in notifiers:
                        skip_tasks.append(notifiers[notifier_name].skip(message=f'Trigger {trigger_name} skipped'))
                        skip_names.append(notifier_name)
                    else:
                        logger.warning(
                            f'Notifier "{notifier_name}" not found for skip',
                            extra={'trigger': trigger_name, 'notifier': notifier_name}
                        )
                if skip_tasks:
                    results = await asyncio.gather(*skip_tasks, return_exceptions=True)
                    for name, result in zip(skip_names, results):
                        if isinstance(result, Exception):
                            logger.warning(
                                f'Error notifying {name} about skip: {result}',
                                extra={'trigger': trigger_name, 'notifier': name}
                            )
                return JSONResponse(status_code=status.HTTP_200_OK, content={'status': 'skipped'})

            logger.info(
                f'Trigger "{trigger_name}" matched, processing',
                extra={'trigger': trigger_name}
            )

            try:
                message = trigger.message.text.format(**body)
            except KeyError as e:
                missing_field = str(e)
                logger.error(
                    f'Missing required field in message template: {missing_field}',
                    extra={'trigger': trigger_name, 'field': missing_field}
                )
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={'error': f'Missing field in template: {missing_field}'}
                )
            except Exception as e:
                logger.error(f'Error formatting message: {e}', extra={'trigger': trigger_name})
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={'error': 'Invalid message template'}
                )

            errors = []
            send_tasks = []
            send_names = []
            for notifier_name in trigger.notify:
                if notifier_name in notifiers:
                    send_tasks.append(notifiers[notifier_name].send(message=message))
                    send_names.append(notifier_name)
                else:
                    logger.error(
                        f'Notifier "{notifier_name}" not found',
                        extra={'trigger': trigger_name, 'notifier': notifier_name}
                    )
                    errors.append(f'Notifier "{notifier_name}" not found')

            if send_tasks:
                results = await asyncio.gather(*send_tasks, return_exceptions=True)
                for name, result in zip(send_names, results):
                    if isinstance(result, Exception):
                        logger.error(
                            f'Error sending notification via {name}: {result}',
                            extra={'trigger': trigger_name, 'notifier': name}
                        )
                        errors.append(f'Failed to notify {name}')
                    else:
                        logger.debug(
                            f'Notification sent via {name}',
                            extra={'trigger': trigger_name, 'notifier': name}
                        )

            if errors:
                logger.warning(
                    f'Trigger "{trigger_name}" processed with errors',
                    extra={'trigger': trigger_name, 'errors': errors}
                )
                return JSONResponse(
                    status_code=status.HTTP_207_MULTI_STATUS,
                    content={'errors': errors}
                )

            logger.info(f'Trigger "{trigger_name}" successfully processed', extra={'trigger': trigger_name})
            return JSONResponse(status_code=status.HTTP_200_OK, content={'status': 'ok'})

        except HTTPException as e:
            logger.warning(
                f'Auth error: {e.detail}',
                extra={'trigger': trigger_name}
            )
            return JSONResponse(status_code=e.status_code, content={'error': e.detail})
        except Exception as e:
            logger.exception(
                f'Unexpected error processing trigger "{trigger_name}": {e}',
                extra={'trigger': trigger_name}
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={'error': 'Internal server error'}
            )

    _endpoint.__name__ = f'trigger_{trigger_name}_handler'
    return _endpoint


def register_routes(
    app: FastAPI,
    triggers: Dict[str, Trigger],
    notifiers: Dict[str, Notifier],
    auths: Optional[Dict[str, Auth]] = None
) -> None:
    """Register FastAPI routes for each configured trigger.

    Iterates through the provided triggers, creates endpoint handlers, and adds them
    to the FastAPI app with the specified paths, methods, and metadata.

    Args:
        app (FastAPI): The FastAPI application instance to register routes on.
        triggers (Dict[str, Trigger]): Mapping of trigger names to Trigger configuration objects.
        notifiers (Dict[str, Notifier]): Mapping of notifier names to Notifier instances for sending notifications.
        auths (Optional[Dict[str, Auth]]): Mapping of authentication scheme names to Auth handlers.
            Used to validate incoming requests when a trigger specifies an auth scheme.

    Returns:
        None
    """
    if not triggers:
        logger.warning('No triggers configured')
        return

    for trigger_name, trigger in triggers.items():
        if not trigger.path:
            logger.error(f'Trigger "{trigger_name}" has no path')
            continue

        if not trigger.notify:
            logger.warning(f'Trigger "{trigger_name}" has no notifiers')

        methods = trigger.methods or ['POST']
        for method in methods:
            try:
                endpoint = create_endpoint(trigger_name, trigger, notifiers, auths)
                app.add_api_route(
                    path=trigger.path,
                    endpoint=endpoint,
                    methods=[method],
                    tags=trigger.tags or ['Triggers'],
                    summary=trigger.name or trigger_name,
                    description=getattr(trigger, 'description', None)
                )
                logger.info(
                    f'Registered route: {method.upper()} {trigger.path}',
                    extra={'trigger': trigger_name, 'method': method}
                )
            except Exception as e:
                logger.error(
                    f'Failed to register route for trigger "{trigger_name}": {e}',
                    extra={'trigger': trigger_name}
                )
