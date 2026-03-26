<p align="center">
  <img src="https://img.shields.io/badge/Draw.io_XML-Source_of_Truth-blue?style=for-the-badge" alt="Draw.io XML" />
  <img src="https://img.shields.io/badge/AWS-35%2B_Services-FF9900?style=for-the-badge&logo=amazon-aws&logoColor=white" alt="AWS Services" />
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/FastAPI-API--First-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Docker-Containerized-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Developed_with-OpenCode_in_Terminal-000000?style=for-the-badge" alt="Developed with OpenCode" />
  <img src="https://img.shields.io/badge/Recommended_Model-Claude_Opus_4.6-cc785c?style=for-the-badge&logo=anthropic&logoColor=white" alt="Claude Opus 4.6" />
</p>

# aws-archsmith

**AI-first AWS architecture automation where Draw.io XML is the single source of truth.**

Describe your infrastructure in plain language. Archsmith generates deterministic Draw.io diagrams with official AWS4 icons, validates structure and layout, and renders publication-ready PNGs -- all without leaving the terminal.

> This entire project -- every line of code, every configuration file, every agent definition -- was developed exclusively with [OpenCode](https://opencode.ai) in the terminal. No IDE. No GUI. Pure CLI-driven AI development.

---

## Table of Contents

- [Three Ways to Use Archsmith](#three-ways-to-use-archsmith)
- [Way 1: OpenCode Interactive](#way-1-opencode-interactive)
- [Way 2: OpenCode Headless](#way-2-opencode-headless)
- [Way 3: Node.js CLI (Direct)](#way-3-nodejs-cli-direct)
- [Recommended Model: Claude Opus 4.6](#recommended-model-claude-opus-46)
- [Features](#features)
- [Architecture Overview](#architecture-overview)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Supported AWS Services (35+)](#supported-aws-services-35)
- [API Reference](#api-reference)
- [Hybrid Skill Integration](#hybrid-skill-integration-drawio-skills)
- [Diagram Mechanics](#diagram-mechanics)
- [Repository Layout](#repository-layout)
- [QA and Validation](#qa-and-validation)
- [Environment Variables](#environment-variables)
- [Contributing](#contributing)
- [License](#license)

---

## Three Ways to Use Archsmith

Archsmith is designed to meet you where you are. Whether you prefer a conversational agent, a CI/CD pipeline, or direct programmatic control, there is a first-class path:

| Mode | Best For | Requires AI Model | Produces |
|---|---|---|---|
| **OpenCode Interactive** | Conversational architecture design from the terminal | Yes (Claude Opus 4.6 recommended) | `.drawio` + `.spec.yaml` + PNG |
| **OpenCode Headless** | CI/CD pipelines, batch operations, scripted workflows | Yes (Claude Opus 4.6 recommended) | `.drawio` + `.spec.yaml` |
| **Node.js CLI (Direct)** | Programmatic generation from YAML specs, no AI needed | No | `.drawio` + `.spec.yaml` + `.arch.json` |

---

## Way 1: OpenCode Interactive

The full conversational experience. You talk to the agent in natural language, it generates and modifies AWS architecture diagrams through slash commands.

### Setup

```bash
# 1. Install OpenCode (https://opencode.ai)
# 2. Clone and enter the repo
git clone https://github.com/Tetfretguru/aws-archsmith.git
cd aws-archsmith

# 3. Install Node.js dependencies (for the external drawio-skills engine)
npm install

# 4. Launch OpenCode in the project directory
opencode
```

### Your First Diagram

```text
> /arch-bootstrap                    # Start Docker API + create session

> /arch-redefine-apply Create an architecture with API Gateway,
  Lambda, and DynamoDB. API Gateway connects to Lambda,
  Lambda connects to DynamoDB.
```

That is it. Archsmith will:

1. Start the Docker API container
2. Generate the `.drawio` XML with official AWS4 icons
3. Convert it to a YAML spec (`.spec.yaml`)
4. Regenerate with professional `tech-blue` theme
5. Validate the output (both native and skill validators)

### Iterating on Your Diagram

```text
> /arch-redefine-apply Add an ElastiCache Redis cluster between Lambda and DynamoDB

> /arch-redefine-apply Add CloudFront in front of API Gateway with dark theme

> /arch-understand                   # See what the diagram contains

> /arch-theme academic               # Switch to grayscale academic theme
```

### All Slash Commands

| Command | What It Does |
|---|---|
| `/arch-bootstrap` | Start Docker + API + create session |
| `/arch-bootstrap postgres` | Same but with PostgreSQL backend |
| `/arch-redefine-apply <prompt>` | Create or modify diagram (with visual polish) |
| `/arch-redefine-apply-raw <prompt>` | Create or modify diagram (native API only, no theme) |
| `/arch-redefine-plan <prompt>` | Preview changes without applying them |
| `/arch-understand` | Inspect current diagram structure |
| `/arch-generate <spec>` | Generate from a YAML spec or built-in example |
| `/arch-to-spec` | Export current `.drawio` to YAML spec |
| `/arch-theme <theme>` | Re-generate with a different visual theme |
| `/arch-start` | Start a session without Docker rebuild |

### Available Themes

| Theme | Best For |
|---|---|
| `tech-blue` (default) | Engineering and system architecture |
| `academic` | IEEE/paper figures, grayscale-safe |
| `academic-color` | Paper figures with color |
| `nature` | Organic, green palettes |
| `dark` | Dark mode presentations |
| `high-contrast` | Accessibility and print |

### Built-in Example Specs

You can generate from any of these without writing YAML:

```text
> /arch-generate cloud-reference-architecture
> /arch-generate microservices
> /arch-generate e-commerce
> /arch-generate login-flow
```

Full list: `cloud-reference-architecture`, `login-flow`, `microservices`, `e-commerce`, `neural-network`, `ablation-study-pipeline`, `ieee-network-paper`, `replicated-brand-flow`, `research-pipeline`, `swimlane-engineering-review`, `system-architecture-paper`.

---

## Way 2: OpenCode Headless

Run Archsmith non-interactively for CI/CD pipelines, batch processing, or scripted workflows. OpenCode's headless mode sends a single prompt and exits.

### Basic Usage

```bash
# Generate a diagram in one shot
opencode -p "Use /arch-bootstrap then /arch-redefine-apply Create API Gateway, Lambda, DynamoDB connected in sequence"

# Modify an existing diagram
opencode -p "Use /arch-redefine-apply Add an S3 bucket for static assets connected to CloudFront"
```

### CI/CD Example (GitHub Actions)

```yaml
name: Generate Architecture Diagram
on:
  push:
    paths: ['architecture/specs/*.yaml']

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install dependencies
        run: npm install

      - name: Start API
        run: |
          docker compose -f docker/compose.api.yml up -d --build api
          sleep 5
          curl --retry 10 --retry-delay 2 http://127.0.0.1:8000/health

      - name: Generate diagram
        run: |
          opencode -p "Use /arch-bootstrap then /arch-redefine-apply Create the architecture described in architecture/specs/my-service.spec.yaml with tech-blue theme"

      - name: Validate
        run: python3 scripts/validate_drawio.py architecture/raw/
```

### Batch Processing

```bash
# Process multiple specs
for spec in architecture/specs/*.spec.yaml; do
  name=$(basename "$spec" .spec.yaml)
  opencode -p "Use /arch-generate $spec with theme tech-blue"
done
```

---

## Way 3: Node.js CLI (Direct)

No AI model required. Use the external `drawio-skills` engine directly to generate `.drawio` files from YAML specs, convert existing diagrams to specs, or switch themes programmatically.

### Generate from a YAML Spec

```bash
# From a built-in example
node .agents/skills/drawio/scripts/cli.js \
  .agents/skills/drawio/references/examples/microservices.spec.yaml \
  architecture/raw/microservices.drawio \
  --theme tech-blue \
  --validate \
  --write-sidecars

# Output:
#   Spec validation: PASSED
#   XML validation: PASSED
#   Saved: architecture/raw/microservices.drawio
```

### Convert an Existing Diagram to YAML Spec

```bash
node .agents/skills/drawio/scripts/cli.js \
  architecture/raw/my-diagram.drawio \
  architecture/specs/my-diagram.spec.yaml \
  --input-format drawio \
  --export-spec \
  --write-sidecars

# Output:
#   Saved spec: architecture/specs/my-diagram.spec.yaml
#   Saved arch: architecture/specs/my-diagram.arch.json
```

### Switch Theme on an Existing Diagram

```bash
# Convert to spec first, then regenerate with new theme
node .agents/skills/drawio/scripts/cli.js \
  architecture/raw/my-diagram.drawio \
  architecture/specs/my-diagram.spec.yaml \
  --input-format drawio --export-spec --write-sidecars

node .agents/skills/drawio/scripts/cli.js \
  architecture/specs/my-diagram.spec.yaml \
  architecture/raw/my-diagram.drawio \
  --theme dark --validate --write-sidecars
```

### Validate with the Native Validator

```bash
python3 scripts/validate_drawio.py architecture/raw/my-diagram.drawio
```

### Write Your Own YAML Spec

```yaml
meta:
  theme: tech-blue
  layout: horizontal

modules:
  - id: vpc
    label: Production VPC
    style:
      dashed: true

nodes:
  - id: alb
    label: Application Load Balancer
    icon: aws.elastic_load_balancing
    position: { x: 100, y: 200 }

  - id: ecs
    label: ECS Fargate
    icon: aws.ecs
    module: vpc
    position: { x: 400, y: 200 }

  - id: rds
    label: RDS PostgreSQL
    icon: aws.rds
    module: vpc
    position: { x: 700, y: 200 }

edges:
  - from: alb
    to: ecs
    label: HTTP
    type: primary

  - from: ecs
    to: rds
    label: SQL
    type: primary
```

```bash
node .agents/skills/drawio/scripts/cli.js \
  my-spec.yaml architecture/raw/my-infra.drawio \
  --theme tech-blue --validate --write-sidecars
```

### Using the FastAPI Directly (No AI, No Node)

For pure HTTP workflows, start the API and call it with curl:

```bash
# Start
docker compose -f docker/compose.api.yml up -d --build api

# Create session
curl -s -X POST http://127.0.0.1:8000/v1/start | python3 -m json.tool

# Generate diagram
curl -s -X POST http://127.0.0.1:8000/v1/diagram/redefine/apply \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "<your-session-id>",
    "message": "API Gateway, Lambda, DynamoDB connected in sequence",
    "file_name": "serverless-api"
  }' | python3 -m json.tool
```

---

## Recommended Model: Claude Opus 4.6

Archsmith's OpenCode agents (Ways 1 and 2) work best with **Claude Opus 4.6** (`claude-opus-4-6`). We recommend this model for three specific reasons:

### 1. Reliable tool orchestration

Archsmith workflows chain 4-6 tool calls in sequence (bootstrap, redefine-apply, to-spec, generate-with-theme, validate). Opus 4.6 handles multi-step tool pipelines without losing context, dropping parameters, or hallucinating intermediate results. Lesser models frequently break the chain at step 3 or 4.

### 2. Accurate XML manipulation

Draw.io XML requires precise structural edits: cell IDs must be unique, geometry values must not overlap, edges must reference valid source/target IDs, and container/parent hierarchies must remain coherent. Opus 4.6 maintains this structural consistency across incremental edits where other models introduce subtle corruption (duplicate IDs, orphaned edges, broken parent references).

### 3. Long-context architecture reasoning

Real-world architecture diagrams involve 20-50 services across multiple VPCs, subnets, and accounts. The redefine workflow requires the model to understand the full existing diagram (via `/arch-understand`), reason about where new services fit, compute non-overlapping positions, and generate correct edge routing. Opus 4.6's extended context window and reasoning capability handle this without truncation artifacts.

### Configuration

In your OpenCode settings, set the model:

```jsonc
// Provider: Anthropic direct
{ "model": "claude-opus-4-6" }

// Provider: GitHub Copilot
{ "model": "github-copilot/claude-opus-4.6" }

// Provider: AWS Bedrock
{ "model": "us.anthropic.claude-opus-4-6-20250515-v1:0" }
```

Other capable models (Claude Sonnet 4, GPT-4.1) can work for simple diagrams, but for production multi-account architectures with 30+ services, Opus 4.6 is the recommended choice.

---

## Features

| Capability | Description |
|---|---|
| **Natural language to diagrams** | Describe AWS architectures in plain English; Archsmith generates valid Draw.io XML |
| **Official AWS4 icons** | Uses `mxgraph.aws4.*` stencils matching the official Draw.io AWS palette |
| **Incremental updates** | Add, remove, reconnect services on existing diagrams without replacing them |
| **Validation-first** | Structure, overlap, and orthogonal edge checks run before every render |
| **6 visual themes** | Professional styling via YAML spec pipeline (tech-blue, academic, dark, etc.) |
| **Docker rendering** | PNG/SVG export via headless Draw.io Desktop container |
| **API-first architecture** | Full FastAPI server with session management, SQLite/Postgres persistence |
| **OpenCode agent integration** | Custom agents, skills, tools, and slash commands for terminal-native workflow |
| **Compressed file support** | Read and redefine both uncompressed and compressed `.drawio` files |
| **Dynamic boundary detection** | Automatic VPC/subnet/account boundary classification using style + geometry heuristics |

---

## Architecture Overview

```
                         User / AI Agent
  (Natural language: "Add API Gateway, Lambda, and DynamoDB")
                              |
              +---------------+---------------+
              |                               |
      OpenCode Agent                    Direct CLI / curl
    (Way 1 or Way 2)                   (Way 3)
              |                               |
   +----------+-----------+                   |
   |                      |                   |
   v                      v                   v
Native Archsmith API   External drawio-skills Engine
  (FastAPI :8000)        (Node.js CLI)
   |                      |
   | structural           | visual
   | mutations            | theming
   |                      |
   +----------+-----------+
              |
              v
     .drawio XML  ------>  validate_drawio.py
   (architecture/raw/)          |
              |                 v
              v            Pass / Fail
     Docker Renderer
       (PNG / SVG)
   (architecture/rendered/)
```

The **enhanced pipeline** (used by `/arch-redefine-apply`) chains both engines:

```
Native redefine-apply  -->  to-spec (YAML)  -->  regenerate with theme  -->  validate
   (structure)              (extract)              (visual polish)          (quality gate)
```

---

## Prerequisites

| Dependency | Required | Notes |
|---|---|---|
| **Python** 3.10+ | Yes | Core engine, API server, validation |
| **Node.js** 18+ | Yes | External drawio-skills engine |
| **Docker** + Compose v2 | Yes | API container and PNG rendering |
| **Poetry** 1.8+ | Recommended | Python dependency management |
| **OpenCode** | For Ways 1 & 2 | Agent mode with custom tools and commands |

---

## Installation

```bash
# 1. Clone
git clone https://github.com/Tetfretguru/aws-archsmith.git
cd aws-archsmith

# 2. Python dependencies
pip install poetry && poetry install
# or: pip install fastapi "uvicorn[standard]" sqlalchemy "pydantic>=2.9" "psycopg[binary]"

# 3. Node.js dependencies (for drawio-skills engine)
npm install

# 4. Initialize workspace
mkdir -p architecture/raw architecture/rendered architecture/specs

# 5. Verify
python3 scripts/validate_drawio.py architecture/raw   # should pass (empty dir)
docker compose version                                  # confirm Compose v2
node --version                                          # confirm Node 18+
```

---

## Supported AWS Services (35+)

Archsmith recognizes these services by keyword and maps them to official Draw.io AWS4 icon stencils:

**Ingress / Network Edge** --
`Route 53` `CloudFront` `WAF` `Application Load Balancer` `API Gateway` `Internet Gateway`

**Compute / Orchestration** --
`ECS` `Fargate` `EKS` `EC2` `Lambda` `AWS Batch` `Step Functions`

**Data / Storage / Search** --
`RDS` `Aurora` `PostgreSQL` `MySQL` `DynamoDB` `S3` `ElastiCache / Redis` `OpenSearch` `Redshift` `EFS`

**Messaging / Integration** --
`SQS` `SNS` `Kinesis` `MSK` `Amazon MQ` `EventBridge`

**Security / Identity / Keys** --
`IAM` `KMS` `Secrets Manager` `Cognito` `Shield`

**Observability** --
`CloudWatch` `X-Ray` `CloudTrail`

> Icon rendering uses `mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.<key>` with 78x78 geometry, matching Draw.io's official AWS4 palette.

---

## API Reference

Base URL: `http://127.0.0.1:8000`

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check (includes DB status) |
| `POST` | `/v1/start` | Bootstrap session, run startup checks |
| `POST` | `/v1/chat` | Natural language create/update diagram |
| `POST` | `/v1/diagram/understand` | Inspect active diagram structure |
| `POST` | `/v1/diagram/redefine/plan` | Preview incremental changes (no mutation) |
| `POST` | `/v1/diagram/redefine/apply` | Apply incremental changes to XML |
| `POST` | `/v1/validate` | Validate a `.drawio` file or inline XML |
| `GET` | `/v1/file` | Retrieve XML content by session |
| `GET` | `/v1/session/{session_id}` | Session details and history |

### Core Flow

```
POST /v1/start  -->  session_id

POST /v1/diagram/redefine/apply {
  session_id, message: "API Gateway, Lambda, DynamoDB",
  file_name: "serverless-api"
}  -->  xml_path, xml_content, validation, changed[]

POST /v1/diagram/redefine/apply {
  session_id, message: "add ElastiCache between Lambda and DynamoDB"
}  -->  updated xml, validation, changed[]
```

---

## Hybrid Skill Integration: `drawio-skills`

Archsmith combines two engines in a single repo:

| Layer | Location | Handles | Icon/Theme |
|---|---|---|---|
| **Native (Archsmith)** | `.opencode/skills/` | AWS structural changes, incremental redefine, session management | AWS4 stencils, no theming |
| **External (drawio-skills)** | `.agents/skills/drawio/` | YAML-first design, 6 themes, visual polish, academic figures | 6 themes, math support |

The **decision router**:

- AWS infrastructure change? --> Native skills (`/arch-redefine-apply`)
- Visual refinement or theming? --> External skill (`/arch-theme`, `/arch-generate`)
- Both? --> Enhanced pipeline: native first, then external for polish

### Validation Rule

Any `.drawio` file in `architecture/raw/` must pass `python3 scripts/validate_drawio.py` regardless of which engine generated it.

---

## Diagram Mechanics

### XML Structure

Archsmith generates valid uncompressed Draw.io `mxGraphModel` XML:

- **Vertices**: `mxCell` elements with explicit `mxGeometry` (`x`, `y`, `width`, `height`)
- **Edges**: `mxCell` elements with `edgeStyle=orthogonalEdgeStyle`
- **Boundaries**: VPC (dashed), public/private subnets as container elements
- **Root cells**: `mxCell` ids `0` and `1` are always present

### Layout Strategy

```
Ingress (left/top) --> Compute / Messaging --> Data (right/bottom)
Security and Observability bridge into Compute tier
```

- Minimum spacing: 40px between sibling nodes
- VPC/subnet boundaries: auto-detected via style tokens and geometry heuristics

### Validation Rules

Every mutation triggers validation:

1. **Structure** -- Valid XML root, required base cells, geometry on all vertices
2. **Layout** -- No overlapping sibling nodes (40px minimum gap)
3. **Edges** -- All connectors use orthogonal routing

---

## Repository Layout

```
aws-archsmith/
|-- archsmith                       # Shell wrapper for interactive CLI
|-- opencode.json                   # OpenCode project config and permissions
|-- AGENTS.md                       # Agent behavioral rules
|-- Makefile                        # Make targets for all workflows
|-- pyproject.toml                  # Poetry project definition
|-- package.json                    # Node.js dependencies (js-yaml)
|
|-- scripts/
|   |-- archsmith_cli.py            # Interactive CLI
|   |-- opencode_api_server.py      # FastAPI server
|   |-- generate_xml.py             # Deterministic Draw.io XML generator
|   |-- diagram_ops.py              # Understand, plan, apply operations
|   |-- validate_drawio.py          # XML structure/layout validator
|   |-- session_state.py            # CLI session state
|   |-- render.sh                   # Docker-based PNG/SVG export
|   |-- api_smoke.py                # API smoke test
|   |-- qa_smoke.py                 # QA automation suite
|   +-- api/                        # Pydantic schemas, service layer, DB
|
|-- docker/
|   |-- Dockerfile.api              # Python 3.10 slim + Poetry
|   |-- compose.api.yml             # API service (SQLite + Postgres profiles)
|   +-- compose.yml                 # Renderer (drawio-desktop-headless)
|
|-- architecture/
|   |-- raw/                        # Source .drawio XML files
|   |-- rendered/                   # Generated PNG/SVG outputs
|   +-- specs/                      # YAML specs and arch.json sidecars
|
|-- .opencode/
|   |-- agents/                     # archsmith-plan, archsmith-build, archsmith-qa
|   |-- tools/                      # 8 TypeScript API-backed tools
|   |-- skills/                     # drawio-understand, drawio-redefine, drawio-validate
|   +-- commands/                   # 9 slash commands
|
|-- .agents/skills/drawio/          # External drawio-skills v2.2.0
|   |-- SKILL.md                    # Skill definition and routing
|   |-- references/                 # Workflows, design system docs
|   |-- scripts/                    # CLI, DSL compiler, SVG renderer
|   |-- assets/                     # 6 theme JSON files
|   +-- evals/                      # Evaluation fixtures
|
+-- docs/                           # API.md, USER_GUIDE.md, PRD, etc.
```

---

## QA and Validation

### Automated Smoke Suite

```bash
make qa-smoke
# or: python3 scripts/qa_smoke.py
```

Covers 12 test cases: preflight checks, directory init, XML structure, base cell IDs, geometry, overlap detection, orthogonal edges, render gate, iterative updates, Docker fallback.

### API Smoke Test

```bash
make api-smoke
# or: python3 scripts/api_smoke.py --base-url "http://127.0.0.1:8000"
```

### Manual Validation

```bash
# All files
python3 scripts/validate_drawio.py architecture/raw/

# Single file
python3 scripts/validate_drawio.py architecture/raw/my-diagram.drawio
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `ARCHSMITH_DB_URL` | `sqlite:////data/archsmith.db` | Database connection (SQLite or PostgreSQL) |
| `ARCHSMITH_API_URL` | `http://127.0.0.1:8000` | API base URL (used by OpenCode tools) |

Set automatically in Docker containers. Override only for custom deployments.

---

## Make Targets

```
make help              Show all targets
make init              Create workspace directories
make generate          Generate .drawio XML from prompt
make validate          Validate all .drawio files
make render            Validate + render PNG via Docker
make demo              Generate + validate + render
make api-up            Start API container (SQLite)
make api-up-postgres   Start API container (PostgreSQL)
make api-down          Stop API container
make api-smoke         Run API smoke test
make qa-smoke          Run QA automation suite
make clean             Remove rendered outputs
```

---

## Contributing

1. Fork the repository
2. Create a feature branch from `main`
3. Ensure `make validate` and `make qa-smoke` pass
4. Submit a pull request with a clear description

Development guidelines:
- `ARCHITECT_GUIDELINES.md` -- XML constraints and design rules
- `INSTRUCTIONS.md` -- Required workflow (validation before rendering)
- `AGENTS.md` -- Agent behavioral rules

---

## License

This project is provided as-is for internal and educational use.

---

<p align="center">
  <sub>Built entirely with <a href="https://opencode.ai">OpenCode</a> + <a href="https://www.anthropic.com/claude/opus">Claude Opus 4.6</a> in the terminal.</sub>
</p>
