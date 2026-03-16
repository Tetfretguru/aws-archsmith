---
description: Unified startup for Archsmith API stack and session bootstrap
agent: archsmith-build
---
Run `archsmith_bootstrap`.

- Default mode is `sqlite`.
- If arguments are provided, map `$1` to `mode` and pass through (`sqlite` or `postgres`).

Return:
- API URL
- session_id
- readiness checks
- active file status
- next recommended commands
