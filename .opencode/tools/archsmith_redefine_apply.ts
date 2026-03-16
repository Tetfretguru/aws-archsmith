import { tool } from "@opencode-ai/plugin"

const apiBase = () => process.env.ARCHSMITH_API_URL ?? "http://127.0.0.1:8000"

export default tool({
  description: "Apply diagram redefine changes through Archsmith API",
  args: {
    message: tool.schema.string().describe("Natural language redefine request"),
    session_id: tool.schema.string().optional().describe("Session id with active file context"),
    file_path: tool.schema.string().optional().describe("Optional explicit file path"),
    icon_set: tool.schema.enum(["aws4", "none"]).optional().describe("Icon set for service additions"),
  },
  async execute(args) {
    const response = await fetch(`${apiBase()}/v1/diagram/redefine/apply`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: args.message,
        session_id: args.session_id,
        file_path: args.file_path,
        icon_set: args.icon_set,
      }),
    })

    if (!response.ok) {
      const body = await response.text()
      throw new Error(`redefine apply failed (${response.status}): ${body}`)
    }

    return await response.json()
  },
})
