# API (XML-only)

This API exposes natural-language architecture interaction over HTTP.

Design goals:

- API-first interaction for OpenCode server workflows
- XML-only outputs (`.drawio` source of truth)
- No render behavior in API path
- Containerized runtime

## Run

SQLite default:

```bash
docker compose -f docker/compose.api.yml up -d --build api
```

Postgres profile:

```bash
docker compose -f docker/compose.api.yml --profile postgres up -d --build api-postgres postgres
```

## Endpoints

- `GET /health`
- `POST /v1/start`
- `POST /v1/chat`
- `POST /v1/validate`
- `GET /v1/file`
- `GET /v1/session/{session_id}`

## Core flow

1. `POST /v1/start` to bootstrap session and checks
2. `POST /v1/chat` with natural language prompt
3. Repeat `POST /v1/chat` for incremental deltas
4. Optional: `GET /v1/file` or `POST /v1/validate`

## Request and response examples

Start:

```json
{
  "icon_set": "aws4"
}
```

Chat:

```json
{
  "session_id": "<id>",
  "message": "Add EventBridge and connect EventBridge -> ECS Fargate Task",
  "file_name": "pipeline-design"
}
```

Chat response:

```json
{
  "session_id": "<id>",
  "changed": ["added EventBridge", "connected EventBridge -> ECS Fargate Task"],
  "xml_path": "/workspace/architecture/raw/pipeline-design.drawio",
  "xml_content": "<?xml version='1.0' ...",
  "validation": {
    "ok": true,
    "message": "Validation passed for pipeline-design.drawio"
  }
}
```

Validation only:

```json
{
  "file_path": "pipeline-design.drawio"
}
```

## Notes

- API writes and updates XML under `architecture/raw/`.
- API stores session and operation history in DB.
- SQLite DB path in default container mode: `/data/archsmith.db`.
