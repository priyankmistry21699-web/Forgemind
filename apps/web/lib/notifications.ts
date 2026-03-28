import { apiFetch } from "@/lib/api";
import type {
  Notification,
  NotificationList,
  DeliveryConfig,
  DeliveryConfigList,
} from "@/types/notification";

/** Fetch paginated notifications for the current user. */
export async function fetchNotifications(
  unreadOnly = false,
  offset = 0,
  limit = 50,
): Promise<NotificationList> {
  return apiFetch<NotificationList>(
    `/notifications?unread_only=${unreadOnly}&offset=${offset}&limit=${limit}`,
  );
}

/** Mark a single notification as read. */
export async function markNotificationRead(
  notificationId: string,
): Promise<Notification> {
  return apiFetch<Notification>(`/notifications/${notificationId}/read`, {
    method: "POST",
  });
}

/** Mark all notifications as read. */
export async function markAllRead(): Promise<{ marked: number }> {
  return apiFetch<{ marked: number }>("/notifications/read-all", {
    method: "POST",
  });
}

/** Create a delivery config (webhook, slack, email). */
export async function createDeliveryConfig(data: {
  channel: string;
  config?: Record<string, unknown>;
}): Promise<DeliveryConfig> {
  return apiFetch<DeliveryConfig>("/notifications/delivery", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/** List delivery configs for the current user. */
export async function fetchDeliveryConfigs(): Promise<DeliveryConfigList> {
  return apiFetch<DeliveryConfigList>("/notifications/delivery");
}
