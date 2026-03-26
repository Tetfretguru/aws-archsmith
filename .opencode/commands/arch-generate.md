---
description: Generate a .drawio diagram from a YAML spec using the external drawio-skills engine
agent: archsmith-build
---
Use the `archsmith_drawio_skill` tool with `operation: "generate"`.

Pass `$ARGUMENTS` as the spec name or path. If the argument is a short name like `cloud-reference-architecture` or `login-flow`, the tool resolves it from built-in examples automatically.

If the user specifies a theme (e.g. "with dark theme", "tema tech-blue"), pass the `theme` parameter.

Available themes: `academic`, `academic-color`, `dark`, `high-contrast`, `nature`, `tech-blue`.

Available built-in specs: `cloud-reference-architecture`, `login-flow`, `microservices`, `e-commerce`, `neural-network`, `ablation-study-pipeline`, `ieee-network-paper`, `replicated-brand-flow`, `research-pipeline`, `swimlane-engineering-review`, `system-architecture-paper`.

The tool runs both the external skill CLI validation and the native `validate_drawio.py` validator.

Report: output file path, theme used, validation status, and suggested next commands (`/arch-understand`, `/arch-redefine-apply`).
