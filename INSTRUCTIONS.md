# INSTRUCTIONS

This file is the canonical reference for the AI workflow used in this repo.

Core principle: validation before rendering.

## Required flow (never skip)

1. Generate or update XML in `architecture/raw/`.
2. Validate XML with `scripts/validate_drawio.py`.
3. Render only if validation passes.
4. Return changed XML path, validation status, and PNG path.

## Commands

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

## Multi-account incremental editing

- Keep working on the same file unless the user asks for a new one.
- Add account boundaries (for example EOP, PDV, Datalake) and place services in the correct account.
- Apply deltas only (add/remove/reconnect/reposition).
- Re-run validation after each iteration.
- Re-render and report updated output paths.

## Quality gate

Run smoke QA after significant script updates:

```bash
python3 scripts/qa_smoke.py
```
