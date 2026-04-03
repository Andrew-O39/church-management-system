import type { NotificationRecipientRow } from "lib/types";

type Props = {
  recipient: NotificationRecipientRow;
};

/**
 * Admin-facing recipient label: name + email when available, else UUID as last resort.
 */
export default function RecipientIdentity({ recipient }: Props) {
  const name = recipient.user_full_name?.trim() || "";
  const email = recipient.user_email?.trim() || "";

  if (name && email) {
    return (
      <div className="min-w-0">
        <div className="font-medium text-slate-900">{name}</div>
        <div className="text-slate-600">({email})</div>
      </div>
    );
  }
  if (name) {
    return <div className="font-medium text-slate-900">{name}</div>;
  }
  if (email) {
    return <div className="font-medium text-slate-900">{email}</div>;
  }
  return (
    <span className="font-mono text-xs text-slate-700" title={recipient.user_id}>
      {recipient.user_id}
    </span>
  );
}
