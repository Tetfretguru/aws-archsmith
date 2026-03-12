# INTRUCTIONS

This document explains how an AI agent should operate this repository end-to-end with minimal human intervention.

The repository is intentionally local-first and XML-first:

- Primary artifact: uncompressed Draw.io XML (`.drawio`) in `architecture/raw/`
- Validation gate: `scripts/validate_drawio.py`
- Export target: PNG (default) in `architecture/rendered/`
- CI is on hold; all workflows are local and deterministic

---

## 1) Mission and Operating Model

`aws-archsmith` exists to let an AI agent generate and maintain AWS architecture diagrams from text instructions.

The AI agent must:

1. Translate user intent into diagram structure.
2. Produce valid Draw.io XML.
3. Validate XML and layout constraints.
4. Export PNG only after validation succeeds.
5. Return clear output paths and a concise change summary.

Core principle: **validation before rendering**.

---

## 2) Repository Map and Responsibilities

### `architecture/raw/`

- Source of truth for diagrams.
- Every generated or edited architecture must end here as `*.drawio`.
- Files are expected to be uncompressed Draw.io XML.

### `architecture/rendered/`

- Generated exports for review and sharing.
- `make render` creates PNG files.
- `make render-all` creates PNG + SVG.

### `architecture/specs/`

- Reserved for future structured specs (`.json`/`.yaml`) if needed.
- Not required for current baseline flow.

### `scripts/generate_xml.py`

- Creates deterministic starter Draw.io XML from prompt text.
- Adds VPC/subnet boundaries and orthogonal connectors.

### `scripts/validate_drawio.py`

- Enforces XML structure and diagram rules.
- Detects malformed structure, missing geometry, sibling overlaps, and non-orthogonal edges.

### `scripts/render.sh`

- Exports `*.drawio` to image formats using headless draw.io.
- Supports `png`, `svg`, or `both`.

### `docker/compose.yml`

- Provides a reproducible rendering environment.
- Default command exports PNG.

### `Makefile`

- Single command interface for all supported operations.
- `render` depends on `validate` (hard gate).

### `ARCHITECT_GUIDELINES.md`

- Role and non-negotiable architecture drawing constraints for AI behavior.

---

## 3) Required Runtime Dependencies

The AI agent should verify these are available before heavy work:

- `python3`
- `docker`
- `docker compose`
- `make` (optional but recommended)

If `make` is unavailable, the agent must use direct Python and Docker commands.

---

## 4) Standard AI Workflow (Default)

For every user request, follow this sequence unless the user explicitly requests a different one.

1. Parse intent from user prompt.
2. Generate or update a `.drawio` in `architecture/raw/`.
3. Run XML validation.
4. If validation passes, render PNG.
5. Return:
   - changed XML file path
   - generated PNG path(s)
   - concise explanation of what changed

Never skip step 3.

---

## 5) Commands the AI Agent Should Use

### Initialize folders

```bash
make init
```

Equivalent without make:

```bash
mkdir -p architecture/raw architecture/rendered architecture/specs
```

### Generate a diagram from text intent

```bash
make generate NAME=payments PROMPT="public ALB, ECS service, RDS postgres"
```

Equivalent without make:

```bash
python3 scripts/generate_xml.py --name "payments" --prompt "public ALB, ECS service, RDS postgres"
```

### Validate XML (mandatory before rendering)

```bash
make validate
```

Equivalent without make:

```bash
python3 scripts/validate_drawio.py architecture/raw
```

### Render PNG only (validation-gated in Makefile)

```bash
make render
```

Manual equivalent:

```bash
python3 scripts/validate_drawio.py architecture/raw && docker compose -f docker/compose.yml run --rm renderer
```

### Render PNG + SVG (also validation-gated)

```bash
make render-all
```

---

## 6) Validation Contract (What Must Pass)

`scripts/validate_drawio.py` currently checks:

1. Root XML tag is `<mxfile>`.
2. `./diagram/mxGraphModel/root` exists.
3. Base cell IDs `0` and `1` exist.
4. All vertex cells include valid numeric geometry (`x`, `y`, `width`, `height`).
5. Width/height are positive.
6. Sibling vertex overlap is not allowed.
7. Every edge includes `edgeStyle=orthogonalEdgeStyle`.

If any check fails, rendering must not run.

---

## 7) Diagram Design Rules for the AI Agent

When generating or editing diagrams, the AI agent should preserve these layout heuristics:

- Place public ingress services toward the left/top.
- Place compute services toward center/right.
- Place data services toward right/bottom.
- Keep adequate spacing between siblings.
- Use orthogonal connectors only.
- Keep boundaries explicit (VPC, subnets).

The canonical policy source remains `ARCHITECT_GUIDELINES.md`.

---

## 8) Prompting Guidelines for Humans (for Better Outputs)

Provide intent with these components when possible:

1. **Ingress**: e.g., Route53, CloudFront, ALB, API Gateway
2. **Compute**: e.g., ECS/Fargate, EKS, Lambda, EC2
3. **Data**: e.g., RDS, DynamoDB, S3, ElastiCache
4. **Security/network boundaries**: VPC, public/private subnet expectations
5. **Connectivity order**: e.g., `CloudFront -> ALB -> ECS -> RDS`

Example prompt:

`Create a production web architecture: Route53 and CloudFront in front of an ALB, ECS Fargate services in private subnet, and RDS PostgreSQL in private data tier.`

---

## 9) Error Handling Policy for the AI Agent

When a command fails, the AI agent should:

1. Capture the exact failure signal.
2. Avoid destructive cleanup by default.
3. Propose one concrete fallback path.
4. Continue non-blocked tasks.
5. Report clear remediation steps.

Typical fallback cases:

- If `make` is unavailable: run scripts directly.
- If Docker is unavailable: complete XML generation + validation, then stop before render and report pending export.
- If validation fails: fix XML/layout first, then rerun validation.

---

## 10) Git Hygiene for AI-Managed Changes

When asked to commit, the AI agent should:

1. Review repo status and diffs first.
2. Stage only intended repository files.
3. Use concise commit messages focused on intent.
4. Avoid rewriting history unless explicitly requested.

Suggested commit prefix patterns:

- `feat:` new capability
- `fix:` bug or broken behavior
- `chore:` maintenance/tooling
- `docs:` documentation updates

---

## 11) Suggested Default Session Script (Agent Playbook)

Use this sequence at the beginning of a new architecture request:

1. `make init`
2. `make generate NAME=<diagram> PROMPT="<user intent>"`
3. `make validate`
4. `make render`
5. Reply with:
   - XML path in `architecture/raw/`
   - PNG path in `architecture/rendered/`
   - Short architecture summary

---

## 12) Current Scope and Explicit Non-Goals

In this baseline repository state:

- Image ingestion is intentionally disabled.
- XML is the primary input/output medium.
- CI/GitHub workflow is intentionally deferred.

If these constraints change, update this file and `README.md` together.
