from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.routes import register_routes
from src.config.models import Trigger, Filter, Message
from src.notifiers.base import Notifier


@pytest.fixture
def mock_notifier():
    notifier = AsyncMock(spec=Notifier)
    notifier.send = AsyncMock()
    notifier.skip = AsyncMock()
    return notifier


SAMPLE_PIPELINE = {
    "object_kind": "pipeline",
    "object_attributes": {
        "id": 41357,
        "ref": "test/event-relay",
        "tag": False,
        "sha": "6e02ddb0d5ac7de1b45220b5db3b47d575a3bb3e",
        "before_sha": "8b1aed0ed5d886c23bf3cb5a3790206241f29e93",
        "source": "push",
        "status": "failed",
        "detailed_status": "failed",
        "stages": [
            "test"
        ]
    },
    "commit": {
        "title": "test(.gitlab-ci): Добавлен тестовый pipeline"
    }
}


@pytest.mark.parametrize(
    "filters,expect_send",
    [
        ([{"field": "object_kind", "equals": "pipeline"}], True),
        ([{"field": "object_kind", "equals": "pipeline-failed"}], False),
        ([{"field": "object_kind", "not_equals": "push"}], True),
        ([{"field": "object_kind", "not_equals": "pipeline"}], False),
        ([{"field": "commit.title", "in": [SAMPLE_PIPELINE["commit"]["title"], "other"]}], True),
        ([{"field": "commit.title", "in": ["other"]}], False),
        ([{"field": "commit.title", "exists": True}], True),
        ([{"field": "missing.field", "exists": False}], True),
        ([{"field": "commit.title", "contains": "test"}], True),
        ([{"field": "commit.title", "contains": "nomatch"}], False),
        ([{"field": "commit.title", "regex": r"test.*pipeline"}], True),
        ([{"field": "object_attributes.id", "gt": 40000}], True),
        ([{"field": "object_attributes.id", "gt": 99999}], False),
        ([{"field": "object_attributes.id", "lt": 99999}], True),
        ([{"field": "object_attributes.id", "lt": 40000}], False),
        ([{"field": "commit.title", "startswith": "test"}], True),
        ([{"field": "commit.title", "startswith": "xxxtest"}], False),
        ([{"field": "commit.title", "endswith": "pipeline"}], True),
        ([{"field": "commit.title", "endswith": "xxpipeline"}], False),
    ],
)
def test_parametrized_filters_over_http(mock_notifier, filters, expect_send):
    filter_objs = [Filter(**f) for f in filters]
    trigger = Trigger(
        path='/pb/gitlab/pipeline_param',
        filters=filter_objs,
        message=Message(text='OK'),
        notify=['mock']
    )

    app = FastAPI()
    register_routes(app, {'gitlab_pipeline_param': trigger}, {'mock': mock_notifier})
    client = TestClient(app)

    mock_notifier.reset_mock()
    resp = client.post('/pb/gitlab/pipeline_param', json=SAMPLE_PIPELINE)
    assert resp.status_code == 200
    if expect_send:
        mock_notifier.send.assert_called_once()
    else:
        mock_notifier.skip.assert_called_once()
