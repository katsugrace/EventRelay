import yaml
from pathlib import Path
from typing import List, Dict

from config.models import AppConfig, Trigger


class Config:
    def __init__(self, path: str):
        self.path = Path(path)
        self._config: AppConfig | None = None
        self._path_index: Dict[str, List[Trigger]] = {}
        self.load()

    def load(self):
        with open(self.path, "r") as f:
            raw = yaml.safe_load(f)

        self._config = AppConfig(**raw)
        self._build_index()

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
