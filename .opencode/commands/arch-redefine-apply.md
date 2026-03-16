---
description: Apply incremental architecture redefine changes via API
agent: archsmith-build
---
Load skill `drawio-redefine` and call `archsmith_redefine_apply` with `$ARGUMENTS` as the change request.
If there is no active file, call it in create-from-scratch mode by also providing `file_name` (for example `architecture-<topic>`).
Then load `drawio-validate` and report file path, concrete changes, and validation outcome.
