import { tool } from "@opencode-ai/plugin"

const apiBase = () => process.env.ARCHSMITH_API_URL ?? "http://127.0.0.1:8000"

export default tool({
  description: "Start or resume an Archsmith API session",
  args: {
    session_id: tool.schema.string().optional().describe("Optional existing session id"),
    icon_set: tool.schema.enum(["aws4", "none"]).optional().describe("Icon set for diagram edits"),
  },
  async execute(args) {
    const response = await fetch(`${apiBase()}/v1/start`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: args.session_id,
        icon_set: args.icon_set ?? "aws4",
      }),
    })

    if (!response.ok) {
      const body = await response.text()
      throw new Error(`start request failed (${response.status}): ${body}`)
    }

    const payload = await response.json()
    return JSON.stringify(payload, null, 2)
  },
})
