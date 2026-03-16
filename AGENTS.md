# Archsmith OpenCode Agent Rules

## Mission

Operate this repository as an API-first AWS architecture agent where Draw.io XML is the source of truth.

## Required workflow

1. Understand the target diagram before changing it.
2. Plan structural deltas from user intent.
3. Apply only incremental changes on the same file unless asked otherwise.
4. Validate XML after every mutation.
5. Render only when explicitly requested.

## API-first behavior

- Prefer Archsmith API endpoints over direct local file mutation:
  - `POST /v1/start`
  - `POST /v1/diagram/understand`
  - `POST /v1/diagram/redefine/plan`
  - `POST /v1/diagram/redefine/apply`
  - `POST /v1/validate`
- Keep session continuity with `session_id`.

## Diagram constraints

- Preserve valid uncompressed `.drawio` XML structure.
- Keep edges orthogonal.
- Avoid overlapping service nodes.
- Keep boundary/container semantics coherent (VPC/subnets/accounts or equivalents).

## Output contract

- Always report: file path, validation status, and concrete changes.
- If validation fails, explain the failing rule and propose the next corrective delta.
