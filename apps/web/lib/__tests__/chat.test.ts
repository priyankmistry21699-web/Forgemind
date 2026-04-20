/**
 * Direct tests for lib/chat.ts.
 */
import { describe, expect, it, vi, beforeEach } from "vitest";

const mocks = vi.hoisted(() => ({ apiFetch: vi.fn() }));
vi.mock("@/lib/api", () => ({
  apiFetch: mocks.apiFetch,
  ApiError: class ApiError extends Error {},
}));

import { sendRunChat } from "../chat";

beforeEach(() => {
  mocks.apiFetch.mockReset();
});

describe("sendRunChat()", () => {
  it("POSTs /runs/:id/chat with the message body", async () => {
    mocks.apiFetch.mockResolvedValue({
      reply: "hello",
      command_result: null,
    });
    const out = await sendRunChat("r-1", "hi there");
    expect(mocks.apiFetch).toHaveBeenCalledWith(
      "/runs/r-1/chat",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ message: "hi there" }),
      }),
    );
    expect(out).toEqual({ reply: "hello", command_result: null });
  });

  it("propagates command_result through to the caller", async () => {
    mocks.apiFetch.mockResolvedValue({
      reply: "ran cmd",
      command_result: {
        command: "retry",
        status: "ok",
        detail: "task q-1 reset",
      },
    });
    const out = await sendRunChat("r-1", "retry task q-1");
    expect(out.command_result).toEqual({
      command: "retry",
      status: "ok",
      detail: "task q-1 reset",
    });
  });
});
