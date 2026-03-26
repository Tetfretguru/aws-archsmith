import { tool } from "@opencode-ai/plugin"
import path from "path"

const SKILL_DIR = ".agents/skills/drawio"
const CLI_PATH = `${SKILL_DIR}/scripts/cli.js`
const EXAMPLES_DIR = `${SKILL_DIR}/references/examples`

export default tool({
  description:
    "Generate, convert, or validate Draw.io diagrams using the external drawio-skills engine. " +
    "Operations: generate (YAML spec → .drawio), to-spec (.drawio → YAML spec), theme (re-generate with a different theme). " +
    "Available themes: academic, academic-color, dark, high-contrast, nature, tech-blue. " +
    "Built-in spec examples: cloud-reference-architecture, login-flow, microservices, e-commerce, neural-network, " +
    "ablation-study-pipeline, ieee-network-paper, replicated-brand-flow, research-pipeline, " +
    "swimlane-engineering-review, system-architecture-paper.",
  args: {
    operation: tool.schema
      .enum(["generate", "to-spec", "theme"])
      .describe("Operation to perform"),
    spec: tool.schema
      .string()
      .optional()
      .describe(
        "Path to YAML spec file (for generate/theme). " +
        "Can be a full path or a short name from built-in examples " +
        "(e.g. 'cloud-reference-architecture', 'login-flow', 'microservices')."
      ),
    input: tool.schema
      .string()
      .optional()
      .describe("Path to input .drawio file (for to-spec operation)"),
    output: tool.schema
      .string()
      .optional()
      .describe(
        "Output file path. Defaults to architecture/raw/<name>.drawio for generate/theme, " +
        "or architecture/specs/<name>.spec.yaml for to-spec."
      ),
    theme: tool.schema
      .string()
      .optional()
      .describe(
        "Theme name: academic, academic-color, dark, high-contrast, nature, tech-blue. " +
        "Omit to use the spec default theme."
      ),
    validate: tool.schema
      .boolean()
      .optional()
      .describe("Run CLI validation after generation (default true)"),
    write_sidecars: tool.schema
      .boolean()
      .optional()
      .describe("Emit .spec.yaml and .arch.json sidecars next to output (default true)"),
  },
  async execute(args, context) {
    const op = args.operation

    if (op === "generate" || op === "theme") {
      if (!args.spec) {
        throw new Error("spec is required for generate/theme operations")
      }

      // Resolve spec path: allow short names from built-in examples
      let specPath = args.spec
      if (!specPath.includes("/") && !specPath.endsWith(".yaml") && !specPath.endsWith(".yml")) {
        specPath = path.join(context.worktree, EXAMPLES_DIR, `${specPath}.yaml`)
      } else if (!path.isAbsolute(specPath)) {
        specPath = path.join(context.worktree, specPath)
      }

      // Derive output path
      const baseName = path.basename(specPath, path.extname(specPath))
      const outputPath = args.output
        ? path.isAbsolute(args.output)
          ? args.output
          : path.join(context.worktree, args.output)
        : path.join(context.worktree, "architecture", "raw", `${baseName}.drawio`)

      // Build CLI command args
      const cliArgs: string[] = [specPath, outputPath]

      if (args.theme) {
        // CLI --theme expects a short name (e.g. "dark", "tech-blue"), not a file path
        cliArgs.push("--theme", args.theme)
      }

      if (args.validate !== false) {
        cliArgs.push("--validate")
      }

      if (args.write_sidecars !== false) {
        cliArgs.push("--write-sidecars")
      }

      const cliScript = path.join(context.worktree, CLI_PATH)
      const proc = Bun.spawn(["node", cliScript, ...cliArgs], {
        cwd: context.worktree,
        stdout: "pipe",
        stderr: "pipe",
      })
      const stdout = await new Response(proc.stdout).text()
      const stderr = await new Response(proc.stderr).text()
      const exitCode = await proc.exited

      if (exitCode !== 0) {
        throw new Error(`drawio-skill generate failed (exit ${exitCode}): ${stderr.trim()}`)
      }

      // Run native validator
      const nativeProc = Bun.spawn(["python3", "scripts/validate_drawio.py", outputPath], {
        cwd: context.worktree,
        stdout: "pipe",
        stderr: "pipe",
      })
      const nativeStdout = await new Response(nativeProc.stdout).text()
      const nativeStderr = await new Response(nativeProc.stderr).text()
      await nativeProc.exited

      return JSON.stringify(
        {
          operation: op,
          spec: specPath,
          output: outputPath,
          theme: args.theme ?? "default",
          skill_output: (stderr.trim() + "\n" + stdout.trim()).trim(),
          native_validation: (nativeStdout.trim() + " " + nativeStderr.trim()).trim(),
        },
        null,
        2
      )
    }

    if (op === "to-spec") {
      if (!args.input) {
        throw new Error("input is required for to-spec operation")
      }

      let inputPath = args.input
      if (!path.isAbsolute(inputPath)) {
        inputPath = path.join(context.worktree, inputPath)
      }

      const baseName = path.basename(inputPath, ".drawio")
      const outputPath = args.output
        ? path.isAbsolute(args.output)
          ? args.output
          : path.join(context.worktree, args.output)
        : path.join(context.worktree, "architecture", "specs", `${baseName}.spec.yaml`)

      const cliScript = path.join(context.worktree, CLI_PATH)

      // CLI with output positional arg writes spec to file, with --write-sidecars for .arch.json
      const proc = Bun.spawn(
        ["node", cliScript, inputPath, outputPath, "--input-format", "drawio", "--export-spec", "--write-sidecars"],
        {
          cwd: context.worktree,
          stdout: "pipe",
          stderr: "pipe",
        }
      )
      const stdout = await new Response(proc.stdout).text()
      const stderr = await new Response(proc.stderr).text()
      const exitCode = await proc.exited

      if (exitCode !== 0) {
        throw new Error(`drawio-skill to-spec failed (exit ${exitCode}): ${stderr.trim()}`)
      }

      return JSON.stringify(
        {
          operation: "to-spec",
          input: inputPath,
          output: outputPath,
          skill_output: (stderr.trim() + "\n" + stdout.trim()).trim(),
        },
        null,
        2
      )
    }

    throw new Error(`Unknown operation: ${op}`)
  },
})
