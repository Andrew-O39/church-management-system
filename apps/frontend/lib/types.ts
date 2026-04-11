export type UserRole = "admin" | "group_leader" | "member";

export type PreferredChannel = "whatsapp" | "sms" | "email";

export type MaritalStatus =
  | "single"
  | "married"
  | "widowed"
  | "divorced"
  | "separated"
  | "prefer_not_to_say";

export type JwtTokenResponse = {
  access_token: string;
  token_type: "bearer";
};

export type UserOut = {
  id: string;
  member_id: string | null;
  full_name: string;
  email: string;
  is_active: boolean;
  role: UserRole;
  created_at: string;
};

export type MeResponse = UserOut;

/** GET /api/v1/users/search (admin) — app user picker. */
export type UserSearchItem = {
  user_id: string;
  full_name: string;
  email: string;
  phone_number: string | null;
  role: UserRole;
  member_id: string | null;
  linked_church_member_name: string | null;
  registry_link_status: "unlinked" | "linked_this_member" | "linked_other_member" | null;
};

export type UserSearchResponse = {
  items: UserSearchItem[];
  total: number;
  page: number;
  page_size: number;
};

/** Matches backend `RegisterResponse` from POST /api/v1/auth/register (201). */
export type RegisterResponse = JwtTokenResponse & {
  user: UserOut;
};

export type MemberProfileOut = {
  id: string;
  user_id: string;
  phone_number: string | null;
  contact_email: string | null;
  address: string | null;
  marital_status: MaritalStatus | null;
  date_of_birth: string | null; // YYYY-MM-DD
  baptism_date: string | null;
  confirmation_date: string | null;
  join_date: string | null;
  whatsapp_enabled: boolean;
  sms_enabled: boolean;
  preferred_channel: PreferredChannel;
  created_at: string;
  updated_at: string;
};

export type MemberDetailResponse = {
  member_id: string; // User.id
  full_name: string;
  email: string;
  is_active: boolean;
  role: UserRole;
  created_at: string;
  updated_at: string;
  profile: MemberProfileOut;
};

export type MemberListItem = {
  member_id: string;
  full_name: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  phone_number: string | null;
  contact_email: string | null;
  join_date: string | null;
  preferred_channel: PreferredChannel | null;
};

export type MemberListResponse = {
  items: MemberListItem[];
  total: number;
  page: number;
  page_size: number;
};

export type MemberSelfPatch = {
  full_name?: string;
  phone_number?: string | null;
  contact_email?: string | null;
  address?: string | null;
  whatsapp_enabled?: boolean;
  sms_enabled?: boolean;
  preferred_channel?: PreferredChannel;
};

export type MemberAdminPatch = {
  full_name?: string | null;
  email?: string | null;
  is_active?: boolean | null;
  role?: UserRole | null;
  phone_number?: string | null;
  contact_email?: string | null;
  address?: string | null;
  marital_status?: MaritalStatus | null;
  date_of_birth?: string | null;
  baptism_date?: string | null;
  confirmation_date?: string | null;
  join_date?: string | null;
  whatsapp_enabled?: boolean | null;
  sms_enabled?: boolean | null;
  preferred_channel?: PreferredChannel | null;
};

export type MinistryRoleInMinistry = "member" | "leader" | "coordinator";

export type MinistryListItem = {
  id: string;
  name: string;
  description: string | null;
  is_active: boolean;
  leader_user_id: string | null;
  active_member_count: number;
  created_at: string;
  updated_at: string;
};

export type MinistryListResponse = {
  items: MinistryListItem[];
  total: number;
  page: number;
  page_size: number;
};

export type MinistryMemberRow = {
  membership_id: string;
  user_id: string;
  full_name: string;
  email: string;
  role_in_ministry: MinistryRoleInMinistry;
  is_active: boolean;
  joined_at: string;
};

export type MinistryDetailResponse = {
  id: string;
  name: string;
  description: string | null;
  is_active: boolean;
  leader_user_id: string | null;
  created_at: string;
  updated_at: string;
  members: MinistryMemberRow[];
};

export type MyMinistryItem = {
  ministry_id: string;
  name: string;
  description: string | null;
  ministry_is_active: boolean;
  membership_id: string;
  role_in_ministry: MinistryRoleInMinistry;
  membership_is_active: boolean;
  joined_at: string;
};

export type MyMinistriesResponse = {
  items: MyMinistryItem[];
};

export type EventType =
  | "service"
  | "meeting"
  | "rehearsal"
  | "retreat"
  | "conference"
  | "other";

export type EventVisibility = "public" | "internal";

export type EventListItem = {
  event_id: string;
  title: string;
  description: string | null;
  event_type: EventType;
  start_at: string;
  end_at: string;
  location: string;
  is_active: boolean;
  visibility: EventVisibility;
  ministry_id: string | null;
  ministry_name: string | null;
};

export type EventDetailResponse = EventListItem & {
  created_by_user_id: string;
  created_at: string;
  updated_at: string;
};

export type EventListResponse = {
  items: EventListItem[];
  total: number;
  page: number;
  page_size: number;
};

export type MyEventsResponse = {
  items: EventListItem[];
};

export type EventMemberViewResponse = Omit<
  EventListItem,
  "is_active" | "visibility"
> & {
  is_active: boolean;
  visibility: EventVisibility;
};

export type AttendanceStatus = "present" | "absent" | "excused";

export type AttendanceRow = {
  id: string;
  event_id: string;
  user_id: string;
  member_full_name: string;
  member_email: string | null;
  contact_email: string | null;
  linked_user_id: string | null;
  user_full_name: string | null;
  user_email: string | null;
  status: AttendanceStatus;
  recorded_by_user_id: string;
  created_at: string;
  updated_at: string;
};

export type EventAttendanceListResponse = {
  items: AttendanceRow[];
};

export type MyAttendanceResponse = {
  event_id: string;
  user_id: string;
  status: AttendanceStatus | null;
  recorded: boolean;
};

export type VolunteerRoleListItem = {
  id: string;
  name: string;
  description: string | null;
  ministry_id: string | null;
  ministry_name: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type VolunteerRoleListResponse = {
  items: VolunteerRoleListItem[];
  total: number;
  page: number;
  page_size: number;
};

export type VolunteerAssignmentRow = {
  id: string;
  event_id: string;
  user_id: string;
  member_full_name: string;
  member_email: string | null;
  linked_user_id: string | null;
  linked_user_email: string | null;
  user_full_name: string;
  user_email: string;
  role_id: string;
  role_name: string;
  notes: string | null;
  assigned_by_user_id: string;
  created_at: string;
  updated_at: string;
};

/** Church parish registry (GET /api/v1/church-members/…) */
export type Gender = "male" | "female" | "other" | "unknown" | "prefer_not_to_say";

export type ChurchMembershipStatus =
  | "active"
  | "inactive"
  | "visitor"
  | "transferred"
  | "deceased";

export type ChurchMemberListItem = {
  id: string;
  church_member_id: string;
  full_name: string;
  first_name: string;
  last_name: string;
  registration_number: string | null;
  email: string | null;
  phone: string | null;
  membership_status: ChurchMembershipStatus;
  is_active: boolean;
  is_deceased: boolean;
  linked_user_id: string | null;
  user_id: string | null;
  user_full_name: string | null;
  user_email: string | null;
  joined_at: string;
};

export type ChurchMemberListResponse = {
  items: ChurchMemberListItem[];
  total: number;
  page: number;
  page_size: number;
};

export type ChurchMemberDetailResponse = {
  id: string;
  church_member_id: string;
  first_name: string;
  middle_name: string | null;
  last_name: string;
  full_name: string;
  gender: Gender;
  date_of_birth: string | null;
  phone: string | null;
  email: string | null;
  address: string | null;
  nationality: string | null;
  occupation: string | null;
  marital_status: MaritalStatus | null;
  preferred_language: string | null;
  registration_number: string | null;
  membership_status: ChurchMembershipStatus;
  joined_at: string;
  is_active: boolean;
  is_baptized: boolean;
  baptism_date: string | null;
  baptism_place: string | null;
  is_communicant: boolean;
  first_communion_date: string | null;
  first_communion_place: string | null;
  is_confirmed: boolean;
  confirmation_date: string | null;
  confirmation_place: string | null;
  is_married: boolean;
  marriage_date: string | null;
  marriage_place: string | null;
  spouse_name: string | null;
  father_name: string | null;
  mother_name: string | null;
  emergency_contact_name: string | null;
  emergency_contact_phone: string | null;
  is_deceased: boolean;
  date_of_death: string | null;
  funeral_date: string | null;
  burial_place: string | null;
  cause_of_death: string | null;
  notes: string | null;
  linked_user_id: string | null;
  user_id: string | null;
  user_full_name: string | null;
  user_email: string | null;
  created_at: string;
  updated_at: string;
};

/** GET /api/v1/church-members/stats — parish-office records only (no app-user joins in headline counts). */
export type ChurchMemberStatsResponse = {
  total_members: number;
  active_members: number;
  inactive_members: number;
  visitor_members: number;
  transferred_members: number;
  deceased_members: number;
  male_members: number;
  female_members: number;
  children_members: number;
  young_adult_members: number;
  adult_members: number;
  baptized_members: number;
  confirmed_members: number;
  communicant_members: number;
  married_members: number;
  single_members: number;
  gender_distribution: Record<string, number>;
  /** child | young_adult | adult | unknown (DOB missing) — ages per registry_age rules */
  age_groups: Record<string, number>;
  members_with_accounts: number;
  members_without_accounts: number;
};

/** GET/POST/PATCH/DELETE /api/v1/registry-saved-filters — admin-owned Parish Registry presets */
export type RegistrySavedFilterRecord = {
  id: string;
  name: string;
  filters: Record<string, string>;
  created_at: string;
  updated_at: string;
};

export type RegistrySavedFilterCreateBody = {
  name: string;
  filters: Record<string, string>;
};

export type RegistrySavedFilterPatchBody = {
  name?: string;
  filters?: Record<string, string>;
};

/** GET /api/v1/church-members/?age_group= — derived from date_of_birth vs UTC today */
export type RegistryAgeGroup = "child" | "young_adult" | "adult";

/** POST /api/v1/church-members/ — body matches backend ChurchMemberCreate */
export type ChurchMemberCreateBody = {
  first_name: string;
  last_name: string;
  middle_name?: string | null;
  gender?: Gender;
  date_of_birth?: string | null;
  phone?: string | null;
  email?: string | null;
  address?: string | null;
  nationality?: string | null;
  occupation?: string | null;
  marital_status?: MaritalStatus | null;
  preferred_language?: string | null;
  registration_number?: string | null;
  membership_status?: ChurchMembershipStatus;
  is_active?: boolean;
  joined_at?: string | null;
  is_baptized?: boolean;
  baptism_date?: string | null;
  baptism_place?: string | null;
  is_communicant?: boolean;
  first_communion_date?: string | null;
  first_communion_place?: string | null;
  is_confirmed?: boolean;
  confirmation_date?: string | null;
  confirmation_place?: string | null;
  is_married?: boolean;
  marriage_date?: string | null;
  marriage_place?: string | null;
  spouse_name?: string | null;
  father_name?: string | null;
  mother_name?: string | null;
  emergency_contact_name?: string | null;
  emergency_contact_phone?: string | null;
  is_deceased?: boolean;
  date_of_death?: string | null;
  funeral_date?: string | null;
  burial_place?: string | null;
  cause_of_death?: string | null;
  notes?: string | null;
};

/** PATCH /api/v1/church-members/{id} */
export type ChurchMemberPatchBody = Partial<ChurchMemberCreateBody>;

/** GET /api/v1/church-members/eligible-for-event/{eventId} — each row is an app user; `id` is user id. */
export type EligibleChurchMemberListItem = {
  id: string;
  full_name: string;
  email: string | null;
  phone: string | null;
};

export type EventVolunteerListResponse = {
  items: VolunteerAssignmentRow[];
};

export type MyVolunteerAssignmentItem = {
  assignment_id: string;
  event_id: string;
  event_title: string;
  start_at: string;
  end_at: string;
  location: string;
  role_id: string;
  role_name: string;
  notes: string | null;
};

export type MyVolunteerAssignmentsResponse = {
  items: MyVolunteerAssignmentItem[];
};

export type MyEventVolunteerAssignmentsResponse = {
  items: VolunteerAssignmentRow[];
};

// --- Notifications (Step 11) ---

export type NotificationCategory =
  | "general"
  | "event"
  | "volunteer"
  | "ministry"
  | "system";

export type NotificationAudienceType =
  | "direct_users"
  | "ministry_members"
  | "event_volunteers";

export type NotificationChannel = "in_app" | "sms" | "whatsapp";

export type NotificationRecipientStatus =
  | "pending"
  | "sent"
  | "delivered"
  | "read"
  | "external_only";

export type NotificationDeliveryAttemptStatus =
  | "pending"
  | "sent"
  | "delivered"
  | "failed";

export type MyNotificationItem = {
  notification_id: string;
  title: string;
  body: string;
  category: NotificationCategory;
  channels: string[];
  related_event_id: string | null;
  related_ministry_id: string | null;
  sent_at: string | null;
  created_at: string;
  recipient_status: NotificationRecipientStatus;
  read_at: string | null;
};

export type MyNotificationsResponse = {
  items: MyNotificationItem[];
  total: number;
  page: number;
  page_size: number;
};

export type UnreadCountResponse = {
  unread_count: number;
};

export type NotificationListItem = {
  id: string;
  title: string;
  category: NotificationCategory;
  channels: string[];
  audience_type: NotificationAudienceType;
  related_event_id: string | null;
  related_ministry_id: string | null;
  created_by_user_id: string;
  created_at: string;
  sent_at: string | null;
  recipient_count: number;
};

export type NotificationListResponse = {
  items: NotificationListItem[];
  total: number;
  page: number;
  page_size: number;
};

export type DeliveryAttemptRow = {
  id: string;
  channel: NotificationChannel;
  status: NotificationDeliveryAttemptStatus;
  provider_message_id: string | null;
  error_detail: string | null;
  created_at: string;
  updated_at: string;
};

export type NotificationRecipientRow = {
  id: string;
  user_id: string;
  /** Present when returned from admin notification detail (joined user). */
  user_full_name?: string | null;
  user_email?: string | null;
  status: NotificationRecipientStatus;
  read_at: string | null;
  created_at: string;
  updated_at: string;
  delivery_attempts: DeliveryAttemptRow[];
};

export type DeliverySummary = {
  audience_resolved_count: number;
  channels: string[];
  in_app_recipient_count: number;
  sms_skipped_no_phone: number;
  sms_attempted: number;
  sms_sent: number;
  sms_failed: number;
  whatsapp_skipped_no_phone: number;
  whatsapp_attempted: number;
  whatsapp_sent: number;
  whatsapp_failed: number;
};

export type NotificationDetailResponse = {
  id: string;
  title: string;
  body: string;
  category: NotificationCategory;
  channels: string[];
  audience_type: NotificationAudienceType;
  related_event_id: string | null;
  related_ministry_id: string | null;
  created_by_user_id: string;
  created_at: string;
  updated_at: string;
  sent_at: string | null;
  delivery_summary: DeliverySummary | null;
  recipients: NotificationRecipientRow[];
};

/** POST /api/v1/notifications/ */
export type NotificationCreateRequest = {
  title: string;
  body: string;
  category: NotificationCategory;
  channels: NotificationChannel[];
  audience_type: NotificationAudienceType;
  user_ids?: string[];
  ministry_id?: string;
  event_id?: string;
};

// --- Event reminders (Step 14) ---

export type EventReminderAudienceType = "event_volunteers" | "ministry_members";

export type EventReminderRuleResponse = {
  id: string;
  event_id: string;
  title_override: string | null;
  body_override: string | null;
  audience_type: EventReminderAudienceType;
  channels: string[];
  offset_minutes_before: number;
  is_active: boolean;
  last_run_at: string | null;
  created_by_user_id: string;
  created_at: string;
  updated_at: string;
};

export type EventReminderRuleListResponse = {
  items: EventReminderRuleResponse[];
};

export type EventReminderRuleCreate = {
  audience_type: EventReminderAudienceType;
  channels: NotificationChannel[];
  offset_minutes_before: number;
  title_override?: string | null;
  body_override?: string | null;
  is_active?: boolean;
};

export type EventReminderRulePatch = {
  audience_type?: EventReminderAudienceType;
  channels?: NotificationChannel[];
  offset_minutes_before?: number;
  title_override?: string | null;
  body_override?: string | null;
  is_active?: boolean;
};

export type RunDueRemindersResponse = {
  rules_considered: number;
  reminders_sent: number;
  skipped_not_due: number;
  skipped_already_sent: number;
  skipped_invalid: number;
  failed: number;
  failure_messages: string[];
};

// --- Reports / dashboard (Step 15) — admin only ---

export type DashboardSummaryResponse = {
  total_users: number;
  active_users_last_30_days: number;
  total_ministries: number;
  active_ministries: number;
  upcoming_events_count: number;
  events_this_week: number;
  volunteers_assigned_upcoming: number;
  unread_notifications_total: number;
};

export type AttendanceReportRow = {
  event_id: string;
  event_title: string;
  start_at: string;
  attendance_count: number;
};

export type AttendanceReportResponse = {
  items: AttendanceReportRow[];
};

export type VolunteerLeaderRow = {
  user_id: string;
  full_name: string;
  assignments_count: number;
};

export type VolunteerReportResponse = {
  items: VolunteerLeaderRow[];
};

export type NotificationInsightsResponse = {
  total_notifications_sent: number;
  total_recipients: number;
  in_app_delivered: number;
  in_app_failed: number;
  sms_attempted: number;
  sms_failed: number;
  whatsapp_attempted: number;
  whatsapp_failed: number;
};

// --- Church profile (Step 16.1) — admin-only singleton ---

export type ChurchProfileResponse = {
  id: string | null;
  church_name: string;
  short_name: string | null;
  address: string | null;
  phone: string | null;
  email: string | null;
  created_at: string | null;
  updated_at: string | null;
};

export type ChurchProfileUpdateRequest = {
  church_name: string;
  short_name?: string | null;
  address?: string | null;
  phone?: string | null;
  email?: string | null;
};

// --- Admin exports (Step 16) — print payload from GET .../print ---

export type PrintExportPayload = {
  title: string;
  subtitle: string | null;
  columns: string[];
  rows: (string | number | boolean | null)[][];
  generated_at: string;
  church_name?: string | null;
  address?: string | null;
  phone?: string | null;
  email?: string | null;
  filters_summary?: string | null;
};

