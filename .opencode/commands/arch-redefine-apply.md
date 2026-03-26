---
description: Apply incremental architecture changes with professional visual styling
agent: archsmith-build
---
Load skill `drawio-redefine` and call `archsmith_redefine_apply_enhanced` with `$ARGUMENTS` as the change request.

This tool chains two engines:
1. **Native Archsmith API** applies the structural mutation (add/remove/connect services)
2. **External drawio-skills** polishes the result (converts to YAML spec, regenerates with theme)

If the user specifies a theme (e.g. "with dark theme", "tema tech-blue"), pass the `theme` parameter.
If no theme is specified, default to `tech-blue`.

Available themes: `academic`, `academic-color`, `dark`, `high-contrast`, `nature`, `tech-blue`.

If there is no active file, call it in create-from-scratch mode by also providing `file_name` (for example `architecture-<topic>`).

Then load `drawio-validate` and report:
- file path
- spec path (YAML sidecar)
- theme applied
- concrete structural changes
- validation outcome (both skill and native)
