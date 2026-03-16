import { tool } from "@opencode-ai/plugin"

const apiBase = () => process.env.ARCHSMITH_API_URL ?? "http://127.0.0.1:8000"

export default tool({
  description: "Plan diagram redefine changes through Archsmith API",
  args: {
    message: tool.schema.string().describe("Natural language redefine request"),
    session_id: tool.schema.string().optional().describe("Session id with active file context"),
    file_path: tool.schema.string().optional().describe("Optional explicit file path"),
    file_name: tool.schema.string().optional().describe("Optional target file name when creating from scratch"),
    icon_set: tool.schema.enum(["aws4", "none"]).optional().describe("Icon set for service additions"),
  },
  async execute(args) {
    const response = await fetch(`${apiBase()}/v1/diagram/redefine/plan`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: args.message,
        session_id: args.session_id,
        file_path: args.file_path,
        file_name: args.file_name,
        icon_set: args.icon_set,
      }),
    })

    if (!response.ok) {
      const body = await response.text()
      throw new Error(`redefine plan failed (${response.status}): ${body}`)
    }

    const payload = await response.json()
    return JSON.stringify(payload, null, 2)
  },
})
