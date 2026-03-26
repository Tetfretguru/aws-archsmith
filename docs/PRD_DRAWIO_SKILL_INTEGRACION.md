# PRD: Hybrid Integration of `drawio-skills` into `aws-archsmith`

**Version**: 1.0
**Date**: 2026-03-26
**Owner**: Architecture Team
**Status**: In Progress

---

## 1. Executive Summary

Integrate the external [`drawio-skills`](https://github.com/bahayonghang/drawio-skills) (v2.2.0) as a complementary design and visual refinement layer within `aws-archsmith`. The native Archsmith engine remains the authority for AWS infrastructure diagrams, while the external skill adds YAML-first workflows, themed generation, image replication, and academic/engineering guardrails for non-structural visual tasks.

## 2. Problem Statement

The current workflow excels at:
- Structural generation and incremental evolution of AWS architecture diagrams
- XML validation (structure, layout, edge routing)
- API-first session management with deterministic output

But has gaps in:
- Visual theming and presentation-grade polish
- Replication of reference diagrams from screenshots or images
- Non-AWS diagram types (UML, flowcharts, academic figures, network topology)
- YAML-based specification for repeatable design-system-driven edits

## 3. Goals

| Goal | Metric | Target |
|---|---|---|
| Zero regression on AWS diagrams | All files in `architecture/raw/` pass `validate_drawio.py` | 100% |
| Reduced visual iteration cycles | Manual style/layout adjustment rounds per diagram | -30% |
| Faster first-acceptable-output | Time from prompt to approved diagram (visual cases) | -40% |
| Clear operational routing | User selects correct workflow on first try | >90% |

## 4. Scope

### In Scope (v1)

- Installation and activation of external `drawio` skill via `npx skills add`
- Coexistence with native skills in separate directories (`.agents/skills/` vs `.opencode/skills/`)
- Decision router documentation (when to use which skill system)
- Artifact conventions for hybrid outputs
- README and operational guide updates
- Validation gate enforcement for any diagram entering `architecture/raw/`

### Out of Scope (v1)

- Replacing Archsmith API as the source of truth for AWS infrastructure
- Migrating existing diagrams to YAML sidecar format
- Modifying `validate_drawio.py` to support YAML spec validation
- MCP server integration (optional live browser editing)
- Custom theme creation beyond the 6 built-in themes

## 5. Users and Personas

### Cloud Architect
- **Priority**: Technical accuracy, AWS semantics, validation compliance
- **Primary route**: Native skills (understand -> redefine -> validate)
- **Uses external skill**: Rarely, only for presentation polish after structural work

### Solutions Architect / Technical Writer
- **Priority**: Visual clarity, consistent theming, fast iteration
- **Primary route**: External skill (create/edit/replicate)
- **Uses native skills**: When modifying AWS-specific boundary/connectivity semantics

## 6. Architecture

### Skill System Layout

```
.opencode/skills/                    # Native (Archsmith API-first)
├── drawio-understand/               #   POST /v1/diagram/understand
├── drawio-redefine/                 #   POST /v1/diagram/redefine/{plan,apply}
└── drawio-validate/                 #   POST /v1/validate

.agents/skills/drawio/               # External (YAML-first, offline)
├── SKILL.md                         #   Routing: create / edit / replicate
├── references/                      #   Design system, workflows, docs
│   ├── workflows/                   #   create.md, edit.md, replicate.md
│   ├── docs/                        #   Edge rules, stencils, math, academic
│   └── examples/                    #   YAML spec templates
├── scripts/                         #   CLI, DSL compiler, SVG renderer
│   ├── cli.js                       #   Main entry point
│   ├── dsl/                         #   YAML-to-XML compiler
│   ├── math/                        #   MathJax/LaTeX support
│   └── svg/                         #   SVG generation
└── assets/                          #   6 themes + sample .drawio files
```

### Decision Flow

```
User request arrives
│
├── Contains AWS service keywords (ECS, Lambda, RDS, VPC, etc.)?
│   ├── YES + structural change → Native skills via Archsmith API
│   └── YES + visual-only change → External skill (edit route)
│
├── Is a replicate/redraw from image?
│   └── YES → External skill (replicate route)
│
├── Is academic/paper/IEEE/thesis?
│   └── YES → External skill (academic-paper route)
│
├── Is general diagram (UML, flowchart, org chart)?
│   └── YES → External skill (create route)
│
└── Ambiguous → Start with native understand, then decide
```

### Quality Gate (Unified)

Regardless of which skill generates the output:

1. Any `.drawio` file entering `architecture/raw/` must pass:
   ```bash
   python3 scripts/validate_drawio.py architecture/raw/<file>.drawio
   ```
2. External skill outputs may additionally validate via:
   ```bash
   node .agents/skills/drawio/scripts/cli.js input.yaml output.drawio --validate --write-sidecars
   ```
3. Both validation results must pass before render is triggered.

## 7. Functional Requirements

### FR-1: Skill Installation
The external skill installs to `.agents/skills/drawio/` without modifying `.opencode/skills/`.

### FR-2: Command Routing
- Native commands (`/arch-*`) continue to work unchanged.
- External skill commands (`/drawio create|edit|replicate`) are available when the skill is loaded.
- No command name collisions exist between the two systems.

### FR-3: Artifact Management
- Native route outputs: `.drawio` XML only, in `architecture/raw/`.
- External route outputs: `.drawio` + `.spec.yaml` + `.arch.json` bundle.
- Sidecar files (`.spec.yaml`, `.arch.json`) are optional for AWS production diagrams.

### FR-4: Validation Enforcement
- `scripts/validate_drawio.py` remains the mandatory gate for production artifacts.
- External skill's built-in validation (structure + layout + quality) runs as supplementary check.

### FR-5: Theme Support
Six themes available through external skill:
- `tech-blue` (default for engineering)
- `academic` (grayscale-safe, IEEE)
- `academic-color` (paper figures with color)
- `nature` (green palette)
- `dark` (dark mode presentations)
- `high-contrast` (accessibility)

## 8. Non-Functional Requirements

| Requirement | Specification |
|---|---|
| Backward compatibility | All existing commands, tools, and workflows unchanged |
| No new runtime dependencies | External skill uses Node.js (already present) |
| No mandatory network access | Offline-first; MCP is optional |
| Traceable provenance | Each artifact's generating workflow is identifiable |
| Deterministic output | Same YAML spec produces same `.drawio` XML |

## 9. Risks and Mitigations

| Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|
| Dual source of truth (XML vs YAML spec) | High | Medium | Policy: AWS production = XML-first via Archsmith API. Visual/general = YAML spec. |
| User confusion on which skill to use | Medium | Medium | Decision router in README + clear command namespacing |
| Style/layout divergence between engines | Medium | Low | Unified validation gate; visual review before merge |
| External skill upstream breaking changes | Low | Low | Pin to v2.2.0; vendor lock only on optional layer |

## 10. Implementation Plan

### Phase 0: Alignment (Day 1) -- DONE
- [x] Confirm scope and acceptance criteria
- [x] Review external skill capabilities and compatibility

### Phase 1: Technical Integration (Days 1-2) -- IN PROGRESS
- [x] Install external skill via `npx skills add`
- [x] Verify coexistence with native skills
- [x] Update README with hybrid integration section
- [x] Create this PRD document
- [ ] Verify zero regression on existing diagrams

### Phase 2: Hybrid Workflow (Days 3-4)
- [ ] Create example prompts for each route (AWS, visual, replicate)
- [ ] Test cross-workflow scenario (native structure + external polish)
- [ ] Document troubleshooting guide for common issues

### Phase 3: QA and Hardening (Days 5-6)
- [ ] Run full QA smoke suite (`python3 scripts/qa_smoke.py`)
- [ ] Run API smoke test (`python3 scripts/api_smoke.py`)
- [ ] Validate all existing diagrams in `architecture/raw/`
- [ ] Test external skill CLI on sample YAML specs

### Phase 4: Gradual Adoption (Ongoing)
- [ ] Pilot with 2-3 real diagrams per route
- [ ] Measure KPIs and gather feedback
- [ ] Adjust decision router based on usage patterns

## 11. Acceptance Criteria

1. **Installation**: External skill installed at `.agents/skills/drawio/` with ~70 files, no conflicts with `.opencode/skills/`.
2. **Native unchanged**: All `/arch-*` commands work identically to pre-integration baseline.
3. **AWS validation**: Every `.drawio` in `architecture/raw/` passes `validate_drawio.py`.
4. **Visual case**: At least one diagram created via external skill (create route) produces valid output.
5. **Replicate case**: At least one diagram replicated via external skill produces themed output.
6. **Documentation**: README includes decision router, artifact conventions, and theme reference.

## 12. PR Strategy

| PR | Title | Contents |
|---|---|---|
| **PR 1** | `feat: integrate drawio-skills for hybrid visual workflow` | Skill installation, README update, PRD, validation confirmation |
| **PR 2** | `feat: add hybrid workflow examples and cross-route testing` | Example prompts, sample outputs, troubleshooting guide |
| **PR 3** | `feat: QA hardening for dual-skill coexistence` | Extended smoke tests, regression suite, adoption metrics |

## 13. Reference Commands

```bash
# Install external skill
npx skills add https://github.com/bahayonghang/drawio-skills --skill drawio

# Native validation (mandatory for production)
python3 scripts/validate_drawio.py architecture/raw

# External skill CLI
node .agents/skills/drawio/scripts/cli.js input.yaml output.drawio --validate --write-sidecars

# Render (Docker, native pipeline)
docker compose -f docker/compose.yml run --rm renderer architecture/raw architecture/rendered png

# QA smoke
python3 scripts/qa_smoke.py
```

## 14. Definition of Done

The integration is successful when:
- The team can choose the correct workflow route in seconds
- Visual quality improves measurably for eligible diagram types
- 100% compliance with Archsmith XML validation rules for AWS production diagrams
- Both skill systems coexist without interference or confusion
