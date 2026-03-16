---
name: drawio-validate
description: Validate drawio xml and report pass fail with corrective guidance
compatibility: opencode
---
## Purpose

Ensure architecture XML remains valid after each mutation.

## Workflow

1. Validate by `file_path` whenever possible.
2. If invalid, group errors by structure, layout, and edge routing.
3. Propose a minimal corrective delta.

## Output contract

- file path
- validation status
- concise remediation step when failed
