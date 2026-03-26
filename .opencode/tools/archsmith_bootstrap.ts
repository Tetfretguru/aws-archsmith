import { tool } from "@opencode-ai/plugin"
import path from "path"

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))

const defaultApiUrl = (mode: "sqlite" | "postgres") => {
  if (process.env.ARCHSMITH_API_URL) return process.env.ARCHSMITH_API_URL
  return mode === "postgres" ? "http://127.0.0.1:8001" : "http://127.0.0.1:8000"
}

async function waitForHealth(apiUrl: string, attempts: number, delayMs: number) {
  let lastError = ""
  for (let i = 0; i < attempts; i += 1) {
    try {
      const response = await fetch(`${apiUrl}/health`)
      if (response.ok) {
        return await response.json()
      }
      lastError = `health returned status ${response.status}`
    } catch (err) {
      lastError = err instanceof Error ? err.message : String(err)
    }
    await sleep(delayMs)
  }
  throw new Error(`API health check failed after ${attempts} attempts: ${lastError}`)
}

export default tool({
  description: "Bootstrap Docker API and start Archsmith session",
  args: {
    mode: tool.schema.enum(["sqlite", "postgres"]).optional().describe("Runtime stack mode"),
    icon_set: tool.schema.enum(["aws4", "none"]).optional().describe("Icon mode for session"),
    session_id: tool.schema.string().optional().describe("Optional existing session id"),
    wait_attempts: tool.schema.number().int().min(5).max(120).optional().describe("Health retry attempts"),
    wait_delay_ms: tool.schema.number().int().min(200).max(5000).optional().describe("Delay between retries"),
  },
  async execute(args, context) {
    const mode = args.mode ?? "sqlite"
    const composeFile = path.join(context.worktree, "docker", "compose.api.yml")

    if (mode === "postgres") {
      await Bun.$`docker compose -f ${composeFile} --profile postgres up -d --build api-postgres postgres`.quiet()
    } else {
      await Bun.$`docker compose -f ${composeFile} up -d --build api`.quiet()
    }

    const apiUrl = defaultApiUrl(mode)
    const health = await waitForHealth(apiUrl, args.wait_attempts ?? 45, args.wait_delay_ms ?? 1000)

    const startResponse = await fetch(`${apiUrl}/v1/start`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: args.session_id,
        icon_set: args.icon_set ?? "aws4",
      }),
    })

    if (!startResponse.ok) {
      const body = await startResponse.text()
      throw new Error(`start request failed (${startResponse.status}): ${body}`)
    }

    const startPayload = await startResponse.json()
    const payload = {
      mode,
      api_url: apiUrl,
      health,
      start: startPayload,
      next: [
        "/arch-understand",
        "/arch-redefine-plan <request>",
        "/arch-redefine-apply <request>",
        "/arch-generate <spec-name> (e.g. cloud-reference-architecture)",
        "/arch-to-spec <file.drawio>",
        "/arch-theme <theme-name> (e.g. dark, tech-blue, nature)",
      ],
    }
    return JSON.stringify(payload, null, 2)
  },
})
