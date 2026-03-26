---
description: Convert an existing .drawio diagram to a YAML spec for inspection or re-generation
agent: archsmith-plan
---
Use the `archsmith_drawio_skill` tool with `operation: "to-spec"`.

Pass `$ARGUMENTS` as the input .drawio file path. If only a filename is given without a directory, assume it is in `architecture/raw/`.

The output YAML spec is saved to `architecture/specs/<name>.spec.yaml` by default.

Report: input file, output spec path, extracted services/nodes count, and suggested next commands (`/arch-generate` to regenerate with a different theme, `/arch-redefine-apply` to modify incrementally).
