# Archsmith User Guide

This guide explains how to use Archsmith in interactive mode.

## Start

```bash
./archsmith
```

or:

```bash
python3 scripts/archsmith_cli.py
```

If you have `make`:

```bash
make chat
```

## First session

1. Start the CLI.
2. Run `:start`.
3. Type your architecture in natural language.
4. Archsmith generates XML, validates it, renders PNG, and reports paths.
5. Keep iterating with more natural-language deltas.

Example:

```text
archsmith> User sends POST to API Gateway and stores in RDS postgres
archsmith> add EventBridge daily trigger and ECS Fargate
archsmith> connect EventBridge -> ECS Fargate Task -> Redshift
```

## Short commands

- `:help` show command list
- `:start` run startup checks and initialize the session
- `:new <name>` create/select a new working file name
- `:use <file>` switch to an existing `.drawio` file
- `:status` show active file and last run state
- `:validate` validate active file
- `:render` validate and render active file
- `:show` quick summary for active diagram
- `:understand [file]` inspect active/existing `.drawio` and print detected structure
- `:redefine <request>` build a no-write redefine plan from natural language
- `:apply` apply the last redefine plan
- `:icon <aws4|none>` choose icon mode for new additions
- `:quit` exit

## Rules of operation

- Natural language lines (without `:`) are treated as change requests.
- Run `:start` first in a fresh session.
- The first natural-language request creates a diagram if none is active.
- Subsequent requests apply incremental updates to the active file.
- Use `:redefine <request>` to preview changes first, then `:apply` to execute.
- `:understand` works with uncompressed and compressed Draw.io files.
- Rendering happens only after validation succeeds.

## Outputs

- XML source: `architecture/raw/<name>.drawio`
- PNG output: `architecture/rendered/<name>.png`

## Troubleshooting

- If validation fails, fix the requested change and run again.
- If render fails, verify `docker` and `docker compose` are available.
- Use `python3 scripts/qa_smoke.py` to run baseline checks.
