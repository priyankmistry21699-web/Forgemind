/**
 * Direct tests for lib/notifications.ts.
 */
import { describe, expect, it, vi, beforeEach } from "vitest";

const mocks = vi.hoisted(() => ({ apiFetch: vi.fn() }));
vi.mock("@/lib/api", () => ({
  apiFetch: mocks.apiFetch,
  ApiError: class ApiError extends Error {},
}));

import {
  fetchNotifications,
  markNotificationRead,
  markAllRead,
  createDeliveryConfig,
  fetchDeliveryConfigs,
} from "../notifications";

beforeEach(() => {
  mocks.apiFetch.mockReset();
});

describe("notifications client", () => {
  it("fetchNotifications uses defaults unread_only=false&offset=0&limit=50", async () => {
    mocks.apiFetch.mockResolvedValue({ items: [], total: 0 });
    await fetchNotifications();
    expect(mocks.apiFetch).toHaveBeenCalledWith(
      "/notifications?unread_only=false&offset=0&limit=50",
    );
  });

  it("fetchNotifications threads unread_only=true", async () => {
    mocks.apiFetch.mockResolvedValue({ items: [], total: 0 });
    await fetchNotifications(true, 10, 5);
    expect(mocks.apiFetch).toHaveBeenCalledWith(
      "/notifications?unread_only=true&offset=10&limit=5",
    );
  });

  it("markNotificationRead POSTs /notifications/:id/read", async () => {
    mocks.apiFetch.mockResolvedValue({ id: "n-1" });
    await markNotificationRead("n-1");
    expect(mocks.apiFetch).toHaveBeenCalledWith("/notifications/n-1/read", {
      method: "POST",
    });
  });

  it("markAllRead POSTs /notifications/read-all and returns the marked count", async () => {
    mocks.apiFetch.mockResolvedValue({ marked: 7 });
    const r = await markAllRead();
    expect(mocks.apiFetch).toHaveBeenCalledWith("/notifications/read-all", {
      method: "POST",
    });
    expect(r).toEqual({ marked: 7 });
  });

  it("createDeliveryConfig POSTs /notifications/delivery with body", async () => {
    mocks.apiFetch.mockResolvedValue({ id: "d-1", channel: "slack" });
    await createDeliveryConfig({
      channel: "slack",
      config: { webhook: "https://slack.test" },
    });
    expect(mocks.apiFetch).toHaveBeenCalledWith(
      "/notifications/delivery",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          channel: "slack",
          config: { webhook: "https://slack.test" },
        }),
      }),
    );
  });

  it("fetchDeliveryConfigs GETs /notifications/delivery", async () => {
    mocks.apiFetch.mockResolvedValue({ items: [], total: 0 });
    await fetchDeliveryConfigs();
    expect(mocks.apiFetch).toHaveBeenCalledWith("/notifications/delivery");
  });
});
