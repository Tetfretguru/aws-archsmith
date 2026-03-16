---
description: Plan incremental architecture redefine changes via API
agent: archsmith-plan
---
Load skill `drawio-redefine` and call `archsmith_redefine_plan` with `$ARGUMENTS` as the change request.
If there is no active file, call it in create-from-scratch mode by also providing `file_name` (for example `architecture-<topic>`).
Return planned changes and expected validation status without applying mutations.
