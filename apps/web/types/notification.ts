/** Notification types matching the backend schemas. */

export type NotificationType =
  | "task_assigned"
  | "task_completed"
  | "approval_required"
  | "approval_granted"
  | "approval_denied"
  | "run_started"
  | "run_completed"
  | "run_failed"
  | "member_added"
  | "member_removed"
  | "escalation"
  | "system";

export type NotificationPriority = "low" | "normal" | "high" | "urgent";

export type DeliveryChannel = "webhook" | "slack" | "email";
export type DeliveryStatus = "active" | "paused" | "disabled";

export interface Notification {
  id: string;
  user_id: string;
  notification_type: NotificationType;
  priority: NotificationPriority;
  title: string;
  body: string | null;
  is_read: boolean;
  resource_type: string | null;
  resource_id: string | null;
  metadata_: Record<string, unknown> | null;
  created_at: string;
}

export interface NotificationList {
  items: Notification[];
  total: number;
  unread_count: number;
}

export interface DeliveryConfig {
  id: string;
  user_id: string;
  channel: DeliveryChannel;
  status: DeliveryStatus;
  config: Record<string, unknown> | null;
  created_at: string;
}

export interface DeliveryConfigList {
  items: DeliveryConfig[];
  total: number;
}
