---
description: Apply incremental architecture changes via native API only (no visual polish)
agent: archsmith-build
---
Load skill `drawio-redefine` and call `archsmith_redefine_apply` with `$ARGUMENTS` as the change request.
If there is no active file, call it in create-from-scratch mode by also providing `file_name` (for example `architecture-<topic>`).
Then load `drawio-validate` and report file path, concrete changes, and validation outcome.

This is the raw native-only mode. For enhanced visual output, use `/arch-redefine-apply` instead.
