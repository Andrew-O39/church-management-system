import type { AuditLogItem } from "lib/types";

/** Maps backend `action` codes to short labels for non-technical admins. */
const ACTION_LABELS: Record<string, string> = {
  // Auth
  "auth.login_success": "Login succeeded",
  "auth.login_failure": "Login failed",
  "auth.register_success": "Account registered",
  // Registry
  "registry.member_create": "Parish record created",
  "registry.member_update": "Parish record updated",
  "registry.member_link_user": "Parish record linked to app user",
  // Exports
  "export.attendance_csv": "Attendance CSV exported",
  "export.attendance_print": "Attendance print export opened",
  "export.volunteers_csv": "Volunteers CSV exported",
  "export.volunteers_print": "Volunteers print export opened",
  "export.app_users_csv": "App users CSV exported",
  "export.app_users_print": "App users print export opened",
  "export.parish_registry_csv": "Parish registry CSV exported",
  "export.parish_registry_print": "Parish registry print export opened",
  // Notifications
  "notification.send": "Notification sent",
  "notification.run_due_reminders": "Due reminders job run",
  // Settings & users
  "church_profile.update": "Church settings updated",
  "app_user.admin_update": "App user updated",
  // Events & operations (Step 19 follow-up)
  "events.create": "Event created",
  "events.update": "Event updated",
  "attendance.create": "Attendance recorded",
  "attendance.update": "Attendance updated",
  "volunteer_assignment.create": "Volunteer assigned",
  "volunteer_assignment.update": "Volunteer assignment updated",
  "volunteer_assignment.delete": "Volunteer assignment removed",
  "ministries.create": "Ministry created",
  "ministries.update": "Ministry updated",
  "volunteer_roles.create": "Volunteer role created",
  "volunteer_roles.update": "Volunteer role updated",
  "event_reminder_rule.create": "Event reminder rule created",
  "event_reminder_rule.update": "Event reminder rule updated",
  "event_reminder_rule.delete": "Event reminder rule deleted",
};

const TARGET_TYPE_LABELS: Record<string, string> = {
  event: "Event",
  church_member: "Parish registry",
  user: "App user",
  export: "Export",
  notification: "Notification",
  notification_job: "Notification job",
  church_profile: "Church profile",
  event_attendance: "Attendance",
  volunteer_assignment: "Volunteer assignment",
  ministry: "Ministry",
  volunteer_role: "Volunteer role",
  event_reminder_rule: "Reminder rule",
  auth: "Sign-in",
};

function titleCaseSegment(s: string): string {
  return s
    .split(/[._]/g)
    .filter(Boolean)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
    .join(" ");
}

export function getAuditActionLabel(action: string): string {
  return ACTION_LABELS[action] ?? titleCaseSegment(action.split(".").pop() ?? action);
}

function metaString(m: Record<string, unknown>, key: string): string | null {
  const v = m[key];
  return typeof v === "string" && v.trim() ? v.trim() : null;
}

/** One-line human context for the “target” column (not raw UUIDs). */
export function getAuditTargetSummary(row: AuditLogItem): string {
  const m = row.metadata_json && typeof row.metadata_json === "object" ? row.metadata_json : {};
  const direct =
    metaString(m, "event_title") ||
    metaString(m, "title") ||
    metaString(m, "name");
  if (direct) return direct;

  const tt = row.target_type;
  if (tt && TARGET_TYPE_LABELS[tt]) return TARGET_TYPE_LABELS[tt];
  if (tt) return titleCaseSegment(tt);
  return "—";
}

export function formatMetadataJson(m: Record<string, unknown>): string {
  try {
    return JSON.stringify(m, null, 2);
  } catch {
    return String(m);
  }
}
