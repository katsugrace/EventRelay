import yaml
import logging
from pathlib import Path
from typing import List, Dict

from src.config.models import AppConfig, Trigger, NotifierConfig, AuthConfig, HelpConfig

logger = logging.getLogger(__name__)


class Config:
    def __init__(self, path: str):
        self.path = Path(path)
        self._config: AppConfig | None = None
        self._path_index: Dict[str, List[Trigger]] = {}
        try:
            self.load()
            logger.info(f'Configuration loaded successfully from {path}')
        except FileNotFoundError:
            logger.error(f'Configuration file not found: {self.path.absolute()}')
            raise
        except yaml.YAMLError as e:
            logger.error(f'Invalid YAML configuration: {e}')
            raise ValueError(f'Invalid YAML in {path}: {e}')
        except Exception as e:
            logger.error(f'Failed to load configuration: {e}')
            raise

    def load(self):
        logger.debug(f'Loading YAML from {self.path}')
        with open(self.path, 'r') as f:
            raw = yaml.safe_load(f)
        if not raw:
            logger.warning('Configuration file is empty')
            raw = {}

        try:
            self._config = AppConfig(**raw)
            self._build_index()
            logger.debug(f'Loaded {len(self._config.triggers)} triggers')
        except ValueError as e:
            logger.error(f'Configuration validation error: {e}')
            raise

    def _build_index(self):
        self._path_index.clear()
        for name, trigger in self._config.triggers.items():
            trigger.name = name
            if trigger.path not in self._path_index:
                self._path_index[trigger.path] = []
            self._path_index[trigger.path].append(trigger)

    def get_all_triggers(self) -> Dict[str, Trigger]:
        return self._config.triggers

    def get_triggers_by_path(self, path: str) -> List[Trigger]:
        return self._path_index.get(path, [])

    def get_all_paths(self) -> List[str]:
        return list(self._path_index.keys())

    def get_notifiers(self) -> Dict[str, NotifierConfig]:
        return self._config.notifiers

    def get_auths(self) -> Dict[str, AuthConfig]:
        return self._config.auths

    def get_helps(self) -> HelpConfig:
        return self._config.helps
