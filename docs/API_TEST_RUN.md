# API Test Run

This document records a manual end-to-end API verification run for the XML-only containerized service.

## Environment

- API stack: `docker/compose.api.yml`
- Runtime mode: SQLite (default)
- Base URL: `http://127.0.0.1:8000`

## Commands executed

1. Start service:

```bash
docker compose -f docker/compose.api.yml up -d --build api
```

2. Health check:

```bash
GET /health
```

3. Session bootstrap:

```bash
POST /v1/start
{
  "icon_set": "aws4"
}
```

4. Natural-language request:

```bash
POST /v1/chat
{
  "session_id": "<session_id>",
  "file_name": "api-endpoint-proof-v2",
  "message": "api gateway, lambda, dynamodb"
}
```

5. Save returned XML payload to a `.drawio` file:

- `architecture/raw/api-endpoint-proof-v2-from-response.drawio`

6. Validate both API-generated and response-saved XML files:

```bash
python3 scripts/validate_drawio.py architecture/raw/api-endpoint-proof-v2.drawio
python3 scripts/validate_drawio.py architecture/raw/api-endpoint-proof-v2-from-response.drawio
```

## Results

- API startup checks: `ready=true`
- Chat response validation: `ok=true`
- Saved response XML file: valid
- Generated XML file: valid

## Artifacts

- Request/response summary: `architecture/specs/api-smoke-result.json`
- Generated XML from API: `architecture/raw/api-endpoint-proof-v2.drawio`
- XML saved from API response body: `architecture/raw/api-endpoint-proof-v2-from-response.drawio`
