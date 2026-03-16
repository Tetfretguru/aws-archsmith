---
name: drawio-understand
description: Understand existing drawio or xml architecture state before changes
compatibility: opencode
---
## Purpose

Inspect the current architecture source before proposing modifications.

## Workflow

1. Call API understand endpoint with session file context.
2. Summarize boundaries, services, unknown components, and inferred flows.
3. Highlight risks that could affect redefine operations.

## Output

- Active file path
- Diagram format and counts
- Notable modeling risks
