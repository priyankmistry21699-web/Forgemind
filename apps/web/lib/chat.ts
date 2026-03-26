import { apiFetch } from "@/lib/api";

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

interface ChatResponse {
  reply: string;
}

/** Send a chat message about a specific run and get a reply. */
export async function sendRunChat(
  runId: string,
  message: string,
): Promise<string> {
  const data = await apiFetch<ChatResponse>(`/runs/${runId}/chat`, {
    method: "POST",
    body: JSON.stringify({ message }),
  });
  return data.reply;
}
