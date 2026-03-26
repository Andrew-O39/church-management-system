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
  full_name: string;
  email: string;
  is_active: boolean;
  role: UserRole;
  created_at: string;
};

export type MeResponse = UserOut;

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

