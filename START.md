# START

This repository is designed for AI-first interactive use.

## OpenCode unified startup

In OpenCode, start everything with one command:

1. Open OpenCode in this repository.
2. Run `/arch-bootstrap`.
3. Wait for API health and session bootstrap response.
4. Continue with `/arch-understand` and redefine commands.

## Universal startup flow

1. Open OpenCode, Claude Code, or Codex in this repository.
2. Type `:start`.
3. Wait for the ready message.
4. Describe your architecture in natural language.

## What `:start` does

- Checks runtime requirements (`python3`, `docker`, `docker compose`).
- Ensures workspace folders exist (`architecture/raw`, `architecture/rendered`, `architecture/specs`).
- Confirms the session is ready for natural-language interaction.

## Ready response contract

After `:start`, the agent should report:

- startup check status (ok/error per item)
- whether the system is ready
- active file status
- next action hint (`:new <name>` or first natural-language prompt)

## First prompts

- `User sends POST to API Gateway and stores in RDS PostgreSQL`
- `Add EventBridge daily trigger and ECS Fargate task`
- `Connect EventBridge -> ECS Fargate Task -> Redshift`
