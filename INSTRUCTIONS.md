# INSTRUCTIONS

This file is the canonical reference for the AI workflow used in this repo.

Core principle: validation before rendering.

## Required flow (never skip)

1. Generate or update XML in `architecture/raw/`.
2. Validate XML with `scripts/validate_drawio.py`.
3. Render only if validation passes.
4. Return changed XML path, validation status, and PNG path.

## Commands

Interactive mode:

```bash
./archsmith
```

or:

```bash
python3 scripts/archsmith_cli.py
```

First command in every session:

```text
:start
```

This initializes startup checks and confirms the workspace is ready.

Short commands available inside interactive mode:

- `:start`
- `:help`
- `:new <name>`
- `:use <file>`
- `:status`
- `:validate`
- `:render`
- `:show`
- `:icon <aws4|none>`
- `:quit`

Generate (AWS icons enabled by default):

```bash
python3 scripts/generate_xml.py --name "payments" --prompt "public ALB, ECS service, RDS postgres"
```

Generate with classic boxes:

```bash
python3 scripts/generate_xml.py --name "payments" --prompt "public ALB, ECS service, RDS postgres" --icon-set none
```

Validate:

```bash
python3 scripts/validate_drawio.py architecture/raw
```

Render:

```bash
docker compose -f docker/compose.yml run --rm renderer architecture/raw architecture/rendered png
```

## API mode (container, XML-only)

Start API with SQLite:

```bash
docker compose -f docker/compose.api.yml up -d --build api
```

Start API with Postgres profile:

```bash
docker compose -f docker/compose.api.yml --profile postgres up -d --build api-postgres postgres
```

API endpoints:

- `GET /health`
- `POST /v1/start`
- `POST /v1/chat`
- `POST /v1/validate`
- `GET /v1/file`
- `GET /v1/session/{session_id}`

API flow never renders images. It only manages XML and validation.

## Multi-account incremental editing

- Keep working on the same file unless the user asks for a new one.
- Add account boundaries (for example EOP, PDV, Datalake) and place services in the correct account.
- Apply deltas only (add/remove/reconnect/reposition).
- Re-run validation after each iteration.
- Re-render and report updated output paths.

Interactive behavior:

- `:start` is the expected first action in a fresh interactive session.
- If there is no active file, the first natural language prompt creates one.
- If there is an active file, natural language input applies deltas (add/remove/connect).
- Validation is mandatory before render.

## Quality gate

Run smoke QA after significant script updates:

```bash
python3 scripts/qa_smoke.py
```
