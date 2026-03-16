import { tool } from "@opencode-ai/plugin"

const apiBase = () => process.env.ARCHSMITH_API_URL ?? "http://127.0.0.1:8000"

export default tool({
  description: "Understand an existing diagram from Archsmith API",
  args: {
    session_id: tool.schema.string().optional().describe("Session id with active file context"),
    file_path: tool.schema.string().optional().describe("Optional explicit file path"),
  },
  async execute(args) {
    const response = await fetch(`${apiBase()}/v1/diagram/understand`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: args.session_id,
        file_path: args.file_path,
      }),
    })

    if (!response.ok) {
      const body = await response.text()
      throw new Error(`understand request failed (${response.status}): ${body}`)
    }

    const payload = await response.json()
    return JSON.stringify(payload, null, 2)
  },
})
