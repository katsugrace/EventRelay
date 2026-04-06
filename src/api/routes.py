from fastapi import FastAPI, Response, status, Request, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any
import logging

from src.config.models import Trigger
from src.filters.engine import TriggerEngine
from src.notifiers.base import Notifier
from src.api.auth.base import Auth

logger = logging.getLogger(__name__)


def create_endpoint(
        trigger_name: str,
        trigger: Trigger,
        notifiers: Dict[str, Notifier],
        auths: Dict[str, Auth] = {}) -> Any:
    engine = TriggerEngine(trigger)

    async def _endpoint(body: Dict[str, Any], request: Request = None) -> Response:
        try:
            if trigger.auth in auths:
                auth = auths[trigger.auth]
                await auth.validate(request)

            logger.info(
                f'Received event for trigger "{trigger_name}"',
                extra={
                    'trigger': trigger_name
                }
            )

            if not engine.check(body):
                logger.debug(
                    f'Trigger "{trigger_name}" conditions not met, skipping',
                    extra={
                        'trigger': trigger_name
                    }
                )

                for notifier_name in trigger.notify:
                    try:
                        notifier = notifiers[notifier_name]
                        await notifier.skip(
                            message=f'Trigger {trigger_name} skipped'
                        )
                    except Exception as e:
                        logger.warning(
                            f'Error notifying {notifier_name} '
                            f'about skip: {e}',
                            extra={
                                'trigger': trigger_name,
                                'notifier': notifier_name
                            }
                        )

                return JSONResponse(
                    status_code=status.HTTP_200_OK,
                    content={
                        'status': 'skipped'
                    }
                )
            logger.info(
                f'Trigger "{trigger_name}" matched, processing',
                extra={
                    'trigger': trigger_name
                }
            )

            try:
                message = trigger.message.text.format(**body)
            except KeyError as e:
                logger.error(
                    f'Missing required field in message template: {e}',
                    extra={
                        'trigger': trigger_name,
                        'field': str(e)
                    }
                )

                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        'error': f'Missing field in template: {e}'
                    }
                )
            except Exception as e:
                logger.error(
                    f'Error formatting message: {e}',
                    extra={
                        'trigger': trigger_name
                    }
                )

                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        'error': 'Invalid message template'
                    }
                )

            errors = []
            for notifier_name in trigger.notify:
                try:
                    notifier = notifiers[notifier_name]
                    await notifier.send(message=message)
                    logger.debug(
                        f'Notification sent via {notifier_name}',
                        extra={
                            'trigger': trigger_name,
                            'notifier': notifier_name
                        }
                    )
                except KeyError:
                    logger.error(
                        f'Notifier "{notifier_name}" not found',
                        extra={'trigger': trigger_name, 'notifier': notifier_name})
                    errors.append(f'Notifier "{notifier_name}" not found')
                except Exception as e:
                    logger.error(
                        f'Error sending notification via {notifier_name}: {e}',
                        extra={
                            'trigger': trigger_name,
                            'notifier': notifier_name
                        }
                    )

                    errors.append(f'Failed to notify {notifier_name}')

            if errors:
                logger.warning(
                    f'Trigger "{trigger_name}" processed with errors',
                    extra={
                        'trigger': trigger_name,
                        'errors': errors
                    }
                )

                return JSONResponse(
                    status_code=status.HTTP_207_MULTI_STATUS,
                    content={
                        'errors': errors
                    }
                )

            logger.info(
                f'Trigger "{trigger_name}" successfully processed',
                extra={'trigger': trigger_name})
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    'status': 'ok'
                }
            )
        except HTTPException as e:
            logger.warning(
                f'Auth error: {e.detail}',
                extra={'trigger': trigger_name})
            return JSONResponse(
                status_code=e.status_code,
                content={
                    'error': e.detail
                }
            )
        except Exception as e:
            logger.exception(
                f'Unexpected error processing trigger "{trigger_name}": {e}',
                extra={
                    'trigger': trigger_name
                }
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    'error': 'Internal server error'
                }
            )

    _endpoint.__name__ = f'trigger_{trigger_name}_handler'
    _endpoint.__doc__ = f'Handle {trigger_name} events'
    return _endpoint


def register_routes(
        app: FastAPI,
        triggers: Dict[str, Trigger],
        notifiers: Dict[str, Notifier],
        auths: Dict[str, Auth] = {}) -> None:
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
                    extra={
                        'trigger': trigger_name,
                        'method': method
                    }
                )
            except Exception as e:
                logger.error(
                    'Failed to register route '
                    f'for trigger "{trigger_name}": {e}',
                    extra={
                        'trigger': trigger_name
                    }
                )
