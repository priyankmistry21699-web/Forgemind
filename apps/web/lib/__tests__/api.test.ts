/**
 * Direct tests for lib/api.ts — the shared fetch wrapper.
 *
 * Mocks the global `fetch` so we can exercise both success and error
 * branches without spinning up the backend.
 */

import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { apiFetch, ApiError, setAuthToken } from "../api";

const originalFetch = globalThis.fetch;

function mockFetch(factory: () => Response | object) {
  // factory returns a fresh response shim per call so bodies aren't re-consumed
  const fn = vi.fn().mockImplementation(async () => factory());
  globalThis.fetch = fn as unknown as typeof fetch;
  return fn;
}

function jsonResponseFactory(status: number, body: unknown) {
  return () =>
    new Response(JSON.stringify(body), {
      status,
      statusText: status === 200 ? "OK" : "Error",
      headers: { "Content-Type": "application/json" },
    });
}

beforeEach(() => {
  // Wipe any token between tests.
  setAuthToken(null);
});

afterEach(() => {
  globalThis.fetch = originalFetch;
  vi.restoreAllMocks();
});

describe("apiFetch()", () => {
  it("returns the parsed JSON body on a 200 response", async () => {
    mockFetch(jsonResponseFactory(200, { ok: true, value: 7 }));
    const result = await apiFetch<{ ok: boolean; value: number }>("/ping");
    expect(result).toEqual({ ok: true, value: 7 });
  });

  it("targets the configured API base URL and path", async () => {
    const fn = mockFetch(jsonResponseFactory(200, {}));
    await apiFetch("/projects");
    const [url] = fn.mock.calls[0];
    // default base URL is http://localhost:8000 in the dev env
    expect(String(url)).toContain("/projects");
    expect(String(url).startsWith("http")).toBe(true);
  });

  it("sends Content-Type: application/json by default and merges request headers", async () => {
    const fn = mockFetch(jsonResponseFactory(200, {}));
    await apiFetch("/x", { headers: { "X-Trace-Id": "t-1" } });
    const [, init] = fn.mock.calls[0];
    const headers = init?.headers as Record<string, string>;
    expect(headers["Content-Type"]).toBe("application/json");
    expect(headers["X-Trace-Id"]).toBe("t-1");
  });

  it("attaches the Bearer token from memory store when present", async () => {
    setAuthToken("tok-abc");
    const fn = mockFetch(jsonResponseFactory(200, {}));
    await apiFetch("/me");
    const [, init] = fn.mock.calls[0];
    const headers = init?.headers as Record<string, string>;
    expect(headers["Authorization"]).toBe("Bearer tok-abc");
  });

  it("does NOT attach an Authorization header when no token is stored", async () => {
    const fn = mockFetch(jsonResponseFactory(200, {}));
    await apiFetch("/me");
    const [, init] = fn.mock.calls[0];
    const headers = init?.headers as Record<string, string>;
    expect(headers["Authorization"]).toBeUndefined();
  });

  it("throws ApiError with parsed JSON body on a 4xx response", async () => {
    mockFetch(jsonResponseFactory(404, { detail: "not found" }));
    try {
      await apiFetch("/missing");
      throw new Error("should have thrown");
    } catch (err) {
      const e = err as ApiError;
      expect(e).toBeInstanceOf(ApiError);
      expect(e.status).toBe(404);
      expect(e.body).toEqual({ detail: "not found" });
      expect(e.name).toBe("ApiError");
      expect(e.message).toMatch(/API 404/);
    }
  });

  it("falls back to response.text() when the error body is non-JSON", async () => {
    // Use an explicit shim so json() can throw WITHOUT consuming the body,
    // letting api.ts fall back to text() — which is the intent of the code.
    const shim = {
      ok: false,
      status: 500,
      statusText: "Server Error",
      async json() {
        throw new SyntaxError("Unexpected token p in JSON");
      },
      async text() {
        return "plain text crash";
      },
    } as unknown as Response;
    mockFetch(() => shim);
    try {
      await apiFetch("/boom");
      throw new Error("should have thrown");
    } catch (err) {
      const e = err as ApiError;
      expect(e).toBeInstanceOf(ApiError);
      expect(e.status).toBe(500);
      expect(e.body).toBe("plain text crash");
    }
  });

  it("forwards method + body through to fetch for mutations", async () => {
    const fn = mockFetch(jsonResponseFactory(200, { id: "1" }));
    await apiFetch("/items", {
      method: "POST",
      body: JSON.stringify({ name: "a" }),
    });
    const [, init] = fn.mock.calls[0];
    expect(init?.method).toBe("POST");
    expect(init?.body).toBe(JSON.stringify({ name: "a" }));
  });
});
