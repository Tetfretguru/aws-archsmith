import { tool } from "@opencode-ai/plugin"

const apiBase = () => process.env.ARCHSMITH_API_URL ?? "http://127.0.0.1:8000"

export default tool({
  description: "Validate diagram XML using Archsmith API",
  args: {
    file_path: tool.schema.string().optional().describe("Relative or absolute .drawio path"),
    xml_content: tool.schema.string().optional().describe("Inline XML content to validate"),
  },
  async execute(args) {
    if (!args.file_path && !args.xml_content) {
      throw new Error("provide file_path or xml_content")
    }

    const response = await fetch(`${apiBase()}/v1/validate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        file_path: args.file_path,
        xml_content: args.xml_content,
      }),
    })

    if (!response.ok) {
      const body = await response.text()
      throw new Error(`validate request failed (${response.status}): ${body}`)
    }

    return await response.json()
  },
})
