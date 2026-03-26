---
description: Re-generate a diagram with a different visual theme using the external drawio-skills engine
agent: archsmith-build
---
Use the `archsmith_drawio_skill` tool with `operation: "theme"`.

Parse `$ARGUMENTS` to extract:
1. The theme name (one of: `academic`, `academic-color`, `dark`, `high-contrast`, `nature`, `tech-blue`)
2. The spec source — either a YAML spec file path or a short example name

If the user references an existing .drawio file instead of a spec, first use `archsmith_drawio_skill` with `operation: "to-spec"` to convert it, then re-generate with the requested theme.

The tool runs both the external skill CLI validation and the native `validate_drawio.py` validator.

Report: output file path, theme applied, validation status, and suggested next commands (`/arch-understand`, `/arch-redefine-apply`).
