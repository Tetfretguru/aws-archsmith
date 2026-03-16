---
name: drawio-redefine
description: Plan and apply incremental architecture redefinitions through API endpoints
compatibility: opencode
---
## Purpose

Execute safe redefine cycles: understand -> plan -> apply -> validate.

## Workflow

1. Use redefine plan endpoint and present proposed deltas.
2. Confirm implied impact in terms of services, edges, and boundaries.
3. Use redefine apply endpoint for the same prompt.
4. Report resulting XML path and validation outcome.

## Constraints

- Keep changes incremental.
- Do not switch files unless explicitly requested.
- Surface validation failures with corrective next delta.
