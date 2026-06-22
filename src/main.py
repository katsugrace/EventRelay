import logging
import sys
from pathlib import Path

from fastapi import FastAPI
from dotenv import load_dotenv

from src.config.loader import Config
from src.env import EnvConfig
from src.api.routes import register_routes
from src.api.status import register_status_routes
from src.notifiers.builder import build_notifiers
from src.api.auth.builder import build_auths

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s][%(name)s][%(levelname)s]: %(message)s'
)

logger = logging.getLogger(__name__)

load_dotenv()

try:
    logger.info('Starting EventRelay application...')
    env = EnvConfig()
    logger.info(f'Configuration file path: {env.config}')

    config_path = Path(env.config)
    if not config_path.exists():
        logger.error(f'Configuration file not found: {config_path.absolute()}')
        sys.exit(1)

    config = Config(path=env.config)
    logger.info('Configuration loaded successfully')

    triggers = config.get_all_triggers()
    if not triggers:
        logger.warning('No triggers configured in the configuration file')

    logger.info(f'Loaded {len(triggers)} triggers')
    notifiers_config = config.get_notifiers()
    if not notifiers_config:
        logger.error('No notifiers configured in the configuration file')
        sys.exit(1)

    logger.info(f'Loaded {len(notifiers_config)} notifiers')
    notifiers = build_notifiers(notifiers_config)
    logger.info(f'Built {len(notifiers)} notifier instances')
    for trigger_name, trigger in triggers.items():
        for notifier_name in trigger.notify:
            if notifier_name not in notifiers:
                logger.error(
                    f'Trigger "{trigger_name}" '
                    'references non-existent '
                    f'notifier "{notifier_name}"'
                )
                sys.exit(1)

    auths = {}
    auths_config = config.get_auths()
    if auths_config:
        logger.info(f'Loaded {len(auths_config)} auths')
        auths = build_auths(auths_config)
        logger.info(f'Built {len(auths)} auth instances')
        for auth_name in auths_config.keys():
            if auth_name not in auths:
                logger.error(
                    f'Auth "{auth_name}" is defined in configuration '
                    'but failed to build an instance'
                )
                sys.exit(1)

    app = FastAPI(title='Event Relay API', version='0.1.0')
    register_routes(
        app=app,
        triggers=triggers,
        notifiers=notifiers,
        auths=auths
    )

    if config.get_helps().status_endpoint:
        register_status_routes(
            app=app,
            triggers=triggers,
            notifiers=notifiers,
            auths=auths
        )
except FileNotFoundError as e:
    logger.error(f'Configuration file error: {e}')
    sys.exit(1)
except ValueError as e:
    logger.error(f'Configuration validation error: {e}')
    sys.exit(1)
except Exception as e:
    logger.exception(f'Failed to initialize application: {e}')
    sys.exit(1)
