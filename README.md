# aws-archsmith

Local-first AWS architecture automation with Draw.io XML as the primary source of truth.

This repository is designed so the AI agent does the implementation work while you drive intent with plain language.

## What it does

- Keeps architecture definitions in uncompressed Draw.io XML (`.drawio`).
- Generates deterministic starter diagrams from plain prompts.
- Validates diagram structure, overlap, and orthogonal edge routing.
- Renders PNG/SVG locally via Docker (CI intentionally on hold).

## Repository layout

```
.
├── architecture/
│   ├── raw/         # source .drawio XML
│   └── rendered/    # generated PNG/SVG
├── docker/
│   └── compose.yml  # local rendering/validation containers
├── scripts/
│   ├── generate_xml.py
│   ├── render.sh
│   └── validate_drawio.py
├── ARCHITECT_GUIDELINES.md
├── Makefile
└── .gitignore
```

## Prerequisites

- Docker
- Docker Compose plugin (`docker compose`)
- Python 3.10+ (only for local generator/validator convenience)

## Quick start

1. Generate XML from an instruction prompt:

```bash
make generate NAME=payments PROMPT="public ALB, ECS service, RDS postgres"
```

2. Validate all `.drawio` files:

```bash
make validate
```

3. Render PNG (after validation) using Docker:

```bash
make render
```

Optional (render PNG + SVG):

```bash
make render-all
```

4. Full demo flow:

```bash
make demo
```

Outputs land in `architecture/rendered/`.

## Notes

- Primary output is XML (`architecture/raw/*.drawio`).
- Image-to-diagram input is intentionally excluded for now.
- CI workflow is intentionally postponed until local flow is stable.
