import { tool } from "@opencode-ai/plugin"
import { readFileSync } from "fs"
import path from "path"

const apiBase = () => process.env.ARCHSMITH_API_URL ?? "http://127.0.0.1:8000"

const SKILL_DIR = ".agents/skills/drawio"
const CLI_PATH = `${SKILL_DIR}/scripts/cli.js`

/**
 * Helper: run a subprocess and collect stdout + stderr.
 * Throws on non-zero exit.
 */
async function run(
  cmd: string[],
  cwd: string,
  label: string
): Promise<{ stdout: string; stderr: string }> {
  const proc = Bun.spawn(cmd, { cwd, stdout: "pipe", stderr: "pipe" })
  const stdout = await new Response(proc.stdout).text()
  const stderr = await new Response(proc.stderr).text()
  const exitCode = await proc.exited
  if (exitCode !== 0) {
    throw new Error(`${label} failed (exit ${exitCode}): ${stderr.trim()}`)
  }
  return { stdout: stdout.trim(), stderr: stderr.trim() }
}

/**
 * Try to read the theme from an existing spec sidecar.
 * Returns null if not found.
 */
function readSpecTheme(specPath: string): string | null {
  try {
    const content = readFileSync(specPath, "utf-8")
    // Quick parse: look for theme: <name> in meta section
    const match = /^\s*theme:\s*["']?([a-z][-a-z0-9]*)["']?\s*$/m.exec(content)
    return match ? match[1] : null
  } catch {
    return null
  }
}

export default tool({
  description:
    "Enhanced redefine-apply: first applies structural changes via the native Archsmith API, " +
    "then polishes the result through the external drawio-skills engine for professional visual " +
    "styling. The pipeline is: native redefine-apply → convert to YAML spec → regenerate .drawio " +
    "with theme. This combines the structural intelligence of the native engine with the visual " +
    "quality of the external skill. " +
    "Available themes: academic, academic-color, dark, high-contrast, nature, tech-blue.",
  args: {
    message: tool.schema.string().describe("Natural language redefine request (e.g. 'Add an ElastiCache Redis connected to Lambda')"),
    session_id: tool.schema.string().optional().describe("Session id with active file context"),
    file_path: tool.schema.string().optional().describe("Optional explicit .drawio file path"),
    file_name: tool.schema.string().optional().describe("Optional target file name when creating from scratch"),
    icon_set: tool.schema.enum(["aws4", "none"]).optional().describe("Icon set for service additions"),
    theme: tool.schema
      .string()
      .optional()
      .describe(
        "Visual theme for the output: academic, academic-color, dark, high-contrast, nature, tech-blue. " +
        "Defaults to tech-blue."
      ),
  },
  async execute(args, context) {
    const cliScript = path.join(context.worktree, CLI_PATH)

    // ── Step 1: Native redefine-apply (structural mutation) ─────────────
    const apiPayload: Record<string, unknown> = {
      message: args.message,
      session_id: args.session_id,
      file_path: args.file_path,
      file_name: args.file_name,
      icon_set: args.icon_set,
    }

    const response = await fetch(`${apiBase()}/v1/diagram/redefine/apply`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(apiPayload),
    })

    if (!response.ok) {
      const body = await response.text()
      throw new Error(`native redefine-apply failed (${response.status}): ${body}`)
    }

    const nativeResult = await response.json() as {
      session_id: string | null
      file_path: string
      changed: string[]
      xml_content: string
      validation: { ok: boolean; message: string }
    }

    // The native engine wrote the file; extract its path
    const drawioPath = nativeResult.file_path
    const baseName = path.basename(drawioPath, ".drawio")

    // ── Step 2: Convert mutated .drawio → YAML spec ────────────────────
    const specPath = path.join(context.worktree, "architecture", "specs", `${baseName}.spec.yaml`)

    // Resolve theme: explicit arg > existing spec sidecar > default
    const existingTheme = readSpecTheme(specPath)
    const theme = args.theme ?? existingTheme ?? "tech-blue"

    const toSpecResult = await run(
      ["node", cliScript, drawioPath, specPath, "--input-format", "drawio", "--export-spec", "--write-sidecars"],
      context.worktree,
      "to-spec"
    )

    // ── Step 3: Regenerate .drawio from spec with theme ────────────────
    const generateArgs = [
      "node", cliScript,
      specPath, drawioPath,
      "--theme", theme,
      "--validate",
      "--write-sidecars",
    ]

    const generateResult = await run(generateArgs, context.worktree, "generate-with-theme")

    // ── Step 4: Native validation on final output ──────────────────────
    const nativeValidation = await run(
      ["python3", "scripts/validate_drawio.py", drawioPath],
      context.worktree,
      "native-validation"
    )

    return JSON.stringify(
      {
        pipeline: "enhanced (native → to-spec → generate-with-theme)",
        session_id: nativeResult.session_id,
        file_path: drawioPath,
        spec_path: specPath,
        theme,
        structural_changes: nativeResult.changed,
        skill_output: (generateResult.stderr + "\n" + generateResult.stdout).trim(),
        native_validation: (nativeValidation.stdout + " " + nativeValidation.stderr).trim(),
      },
      null,
      2
    )
  },
})
