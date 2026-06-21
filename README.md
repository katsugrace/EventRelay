# EventRelay

![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg) ![Tests](https://img.shields.io/badge/tests-pytest-green.svg) ![Coverage Badge](assets/coverage-badge.svg)

Capture events, filter them and send notifications. EventRelay creates API endpoints to receive events, checks them against specified conditions, and sends notifications.

## Installation and Startup

### Requirements
- `Python 3.9+`
- `pip`

### Installing dependencies
```bash
pip install -r requirements.txt
```

### Launch
1. Set the environment variables in `.env` file (optional):
   ```
   CONFIG_PATH=config/triggers.yaml
   HOST=127.0.0.1
   PORT=8000
   TELEGRAM_API=your_telegram_bot_token
   GITLAB_WEBHOOK_SECRET=your_gitlab_webhook_secret
   ```

2. Launch the app:
   ```bash
   ./start.sh
   ```

The app will be available at `http://127.0.0.1:8000`.

## Configuration

The project configuration is stored in a YAML file (by default `config/triggers.yaml`). The file consists of two main sections: `notifiers` и `triggers`.

### Configuration Structure

#### Notifiers
The section specifies the delivery channels (Telegram, mock, etc.):

```yaml
notifiers:
  alerts:
    type: telegram
    token_env: TELEGRAM_BOT_TOKEN
    chat_ids: [123456789]

  test:
    type: mock  # For testing
```

#### Triggers
The section defines the rules for handling events:

```yaml
triggers:
  example_trigger:
    name: Example Trigger                   # Human-readable name
    active: true                            # Is the trigger active?
    description: Example of a trigger for event handling
    path: /webhooks/example                 # API endpoint path
    methods: [POST]                         # HTTP methods
    tags: [Example]                         # Tags for API documentation

    filters:                                # Trigger conditions
      - field: event_type
        equals: push
      - field: repository.name
        equals: my-repo

    message:
      text: "📢 Event: {event_type} in {repository[name]}"  # Message template

    notify:                                 # Which notifiers should I use?
      - alerts
```

### Filter operators

Supported operators for filters:

- `equals`: exact match
- `not_equals`: is not equal to
- `in`: entry in the list
- `exists`: check if a field exists (true/false)
- `contains`: contains the substring
- `regex`: regular expression
- `gt`: more than
- `lt`: less than
- `startswith`: begins with
- `endswith`: ends with

Field `field` supports nested objects via a dot: `object_attributes.status`.

### Example of a complete configuration

```yaml
notifiers:
  telegram_channels:
    type: telegram
    token_env: TELEGRAM_API
    chat_ids: [123456789, 987654321]

  test:
    type: mock

triggers:
  github_push:
    name: GitHub Push Event
    path: /webhooks/github
    methods: [POST]
    tags: [GitHub]

    filters:
      - field: action
        equals: pushed
      - field: repository.name
        equals: my-repo

    message:
      text: "🚀 New push to {repository[full_name]} by {sender[login]}"

    notify:
      - test

  deployment_finished:
    name: Deployment Finished
    path: /events/deployment
    methods: [POST]
    tags: [CI/CD]

    filters:
      - field: status
        equals: success
      - field: environment
        in: [staging, production]

    message:
      text: "✅ Deployment to {environment} completed"

    notify:
      - telegram_channels
      - test
```

## API

EventRelay automatically creates API endpoints based on trigger configurations. Each endpoint accepts POST requests with a JSON body.

### API Documentation
Once the app is launched, the documentation is available at:
- `Swagger UI`: `http://127.0.0.1:8000/docs`
- `ReDoc`: `http://127.0.0.1:8000/redoc`

### Examples of queries

#### GitHub Push Event
```bash
curl -X POST "http://127.0.0.1:8000/webhooks/github" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "pushed",
    "repository": {
      "name": "my-repo",
      "full_name": "user/my-repo"
    },
    "sender": {
      "login": "john-doe"
    }
  }'
```

#### GitLab Merge Request
```bash
curl -X POST "http://127.0.0.1:8000/webhooks/gitlab/mr" \
  -H "Content-Type: application/json" \
  -d '{
    "object_kind": "merge_request",
    "object_attributes": {
      "action": "open",
      "iid": 42,
      "title": "Add new feature",
      "url": "https://gitlab.com/example/project/-/merge_requests/42",
      "target_branch": "main"
    }
  }'
```

## Docker

### Build Image
```bash
docker build -t eventrelay:latest .
```

### Launch
```bash
docker run -d \
  --name eventrelay \
  -p 8022:8022 \
  -e CONFIG_PATH=/app/config/custom.yaml \
  -e TELEGRAM_API=<telegram_api_url> \
  -e GITLAB_WEBHOOK_SECRET=<secret> \
  eventrelay:latest
```

### Parameters
- `CONFIG_PATH`: path to the YAML configuration (by default **config/triggers.yaml**)
- `TELEGRAM_API`: telegram bot token used for sending notifications
- `GITLAB_WEBHOOK_SECRET`: a secret for verifying incoming webhook requests from GitLab
