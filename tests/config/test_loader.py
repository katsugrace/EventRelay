import pytest
from src.config.loader import Config

VALID_YAML = '''
auths:
  test:
    type: mock

notifiers:
  test:
    type: mock

triggers:
  github_push:
    path: /webhooks/github
    filters:
      - field: action
        equals: pushed
    message:
      text: 'Test message'
    notify:
      - test
'''

INVALID_YAML = '''
notifiers:
  test
    type: mock
'''


@pytest.fixture
def valid_config_file(tmp_path):
    file = tmp_path / 'config.yaml'
    file.write_text(VALID_YAML)
    return file


@pytest.fixture
def invalid_config_file(tmp_path):
    file = tmp_path / 'invalid.yaml'
    file.write_text(INVALID_YAML)
    return file


@pytest.fixture
def empty_config_file(tmp_path):
    file = tmp_path / 'empty.yaml'
    file.write_text('')
    return file


def test_load_valid_config(valid_config_file):
    cfg = Config(valid_config_file)
    triggers = cfg.get_all_triggers()
    assert 'github_push' in triggers
    assert triggers['github_push'].path == '/webhooks/github'
    notifiers = cfg.get_notifiers()
    assert 'test' in notifiers
    assert notifiers['test'].type == 'mock'
    auths = cfg.get_auths()
    assert 'test' in auths
    assert auths['test'].type == 'mock'


def test_path_index(valid_config_file):
    cfg = Config(valid_config_file)
    triggers_by_path = cfg.get_triggers_by_path('/webhooks/github')
    assert len(triggers_by_path) == 1
    assert triggers_by_path[0].name == 'github_push'
    assert cfg.get_triggers_by_path('/no/such/path') == []


def test_all_paths(valid_config_file):
    cfg = Config(valid_config_file)
    paths = cfg.get_all_paths()
    assert '/webhooks/github' in paths


def test_file_not_found(tmp_path):
    missing_file = tmp_path / 'missing.yaml'
    with pytest.raises(FileNotFoundError):
        Config(missing_file)


def test_invalid_yaml(invalid_config_file):
    with pytest.raises(ValueError):
        Config(invalid_config_file)


def test_unexpected_exception_is_reraised(valid_config_file, monkeypatch):
    def mock_load(self):
        raise RuntimeError('boom')

    monkeypatch.setattr(Config, 'load', mock_load)
    with pytest.raises(RuntimeError) as exc:
        Config(valid_config_file)

    assert 'boom' in str(exc.value)


def test_empty_yaml_file_logs_warning(empty_config_file, monkeypatch):
    called = {}

    def mock_warning(msg):
        called['msg'] = msg

    monkeypatch.setattr('src.config.loader.logger.warning', mock_warning)
    with pytest.raises(Exception):
        Config(empty_config_file)

    assert 'empty' in called['msg'].lower()
