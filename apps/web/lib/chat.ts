import { apiFetch } from "@/lib/api";

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

interface ChatResponse {
  reply: string;
  command_result: {
    command: string;
    status: string;
    detail?: string;
  } | null;
}

/** Send a chat message about a specific run and get a reply. */
export async function sendRunChat(
  runId: string,
  message: string,
): Promise<{ reply: string; command_result: ChatResponse["command_result"] }> {
  const data = await apiFetch<ChatResponse>(`/runs/${runId}/chat`, {
    method: "POST",
    body: JSON.stringify({ message }),
  });
  return { reply: data.reply, command_result: data.command_result };
}
