# aws-archsmith

Local-first AWS architecture automation with Draw.io XML as the primary source of truth.

This repository is designed so the AI agent does the implementation work while you drive intent with plain language.

## What it does

- Keeps architecture definitions in uncompressed Draw.io XML (`.drawio`).
- Generates deterministic starter diagrams from plain prompts.
- Supports AWS icons via Draw.io AWS4 shapes (`mxgraph.aws4.*`) by default.
- Validates diagram structure, overlap, and orthogonal edge routing.
- Renders PNG/SVG locally via Docker (CI intentionally on hold).

## Diagram mechanics (boxes and arrows)

- Boxes are Draw.io `mxCell` vertices with explicit geometry (`x`, `y`, `width`, `height`).
- Boundaries are also boxes: VPC (dashed) containing Public/Private Subnet containers.
- Arrows are Draw.io edge `mxCell` elements with orthogonal routing and arrowheads.
- The generator groups services by tier and auto-connects flows:
  - ingress chain -> compute/messaging -> data
  - security and observability can bridge into compute
- Validation enforces orthogonal arrows and catches sibling overlaps before render.

## Supported AWS services (keyword driven)

Ingress/network edge:

- Route 53, CloudFront, WAF, Application Load Balancer, API Gateway, Internet Gateway

Compute/orchestration:

- ECS, Fargate, EKS, EC2, Lambda, AWS Batch, Step Functions

Data/storage/search:

- RDS, Aurora, PostgreSQL, MySQL, DynamoDB, S3, ElastiCache/Redis, OpenSearch, Redshift, EFS

Messaging/integration:

- SQS, SNS, Kinesis, MSK, Amazon MQ, EventBridge

Security/identity/keys:

- IAM, KMS, Secrets Manager, Cognito, Shield

Observability:

- CloudWatch, X-Ray, CloudTrail

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

Without `make`:

```bash
python3 scripts/generate_xml.py --name "payments" --prompt "public ALB, ECS service, RDS postgres"
```

Use classic boxes instead of AWS icons:

```bash
python3 scripts/generate_xml.py --name "payments" --prompt "public ALB, ECS service, RDS postgres" --icon-set none
```

2. Validate all `.drawio` files:

```bash
make validate
```

3. Render PNG (after validation) using Docker:

```bash
make render
```

Without `make`:

```bash
python3 scripts/validate_drawio.py architecture/raw && docker compose -f docker/compose.yml run --rm renderer
```

Optional (render PNG + SVG):

```bash
make render-all
```

4. Full demo flow:

```bash
make demo
```

## Iterative multi-account workflow

Use this loop for conversational architecture design:

1. Generate a base diagram from the prompt.
2. Edit the same XML file with incremental deltas (do not replace everything).
3. Re-run validation.
4. Render and share XML + PNG paths.

Recommended commands for a single target file:

```bash
python3 scripts/validate_drawio.py architecture/raw/multi-account-etl.drawio
docker compose -f docker/compose.yml run --rm renderer architecture/raw architecture/rendered png
```

## QA smoke checks

Run the automated smoke suite:

```bash
python3 scripts/qa_smoke.py
```

If `make` is installed:

```bash
make qa-smoke
```

Outputs land in `architecture/rendered/`.

## Notes

- Primary output is XML (`architecture/raw/*.drawio`).
- `architecture/` runtime artifacts are ignored by default in Git (except `.gitkeep`).
- Agent operating workflow and incremental multi-account process are documented in `INSTRUCTIONS.md`.
- Image-to-diagram input is intentionally excluded for now.
- CI workflow is intentionally postponed until local flow is stable.
