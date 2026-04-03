import type { DeliverySummary } from "lib/types";

function plural(n: number, one: string, many: string): string {
  return n === 1 ? one : many;
}

function messageSentPhrase(count: number): string {
  if (count === 0) return "";
  if (count === 1) {
    return "1 message was sent successfully.";
  }
  return `${count} messages were sent successfully.`;
}

function messageFailedPhrase(count: number): string {
  if (count === 0) return "";
  if (count === 1) {
    return "1 message failed due to a delivery error.";
  }
  return `${count} messages failed due to a delivery error.`;
}

function usersSkippedNoPhonePhrase(count: number): string {
  if (count === 0) return "";
  if (count === 1) {
    return "1 user was skipped because no phone number is available.";
  }
  return `${count} users were skipped because no phone numbers are available.`;
}

type Props = {
  summary: DeliverySummary;
  /** Slightly tighter spacing when shown inline after send */
  compact?: boolean;
};

/**
 * Human-readable delivery summary: only sections for channels present in `summary.channels`.
 * Omits zero-only sentences for failed/skipped/sent where noted (clearer than listing “0 failed”).
 */
export default function DeliverySummaryContent({ summary, compact }: Props) {
  const selected = new Set(summary.channels);
  const spaceClass = compact ? "space-y-3" : "space-y-4";

  return (
    <div className={`${spaceClass} text-sm leading-relaxed text-slate-700`}>
      {selected.has("in_app") ? (
        <section>
          <h4 className="font-semibold text-slate-900">In-app delivery</h4>
          <p className="mt-1">
            {summary.in_app_recipient_count > 0 ? (
              <>
                We delivered this notification in the app to {summary.in_app_recipient_count}{" "}
                {plural(summary.in_app_recipient_count, "user", "users")}.
              </>
            ) : (
              <>This notification was not delivered in the app to any users.</>
            )}
          </p>
        </section>
      ) : null}

      {selected.has("sms") ? (
        <section>
          <h4 className="font-semibold text-slate-900">SMS delivery</h4>
          <SmsWhatsappNarrative
            channel="SMS"
            attempted={summary.sms_attempted}
            skippedNoPhone={summary.sms_skipped_no_phone}
            sent={summary.sms_sent}
            failed={summary.sms_failed}
          />
        </section>
      ) : null}

      {selected.has("whatsapp") ? (
        <section>
          <h4 className="font-semibold text-slate-900">WhatsApp delivery</h4>
          <SmsWhatsappNarrative
            channel="WhatsApp"
            attempted={summary.whatsapp_attempted}
            skippedNoPhone={summary.whatsapp_skipped_no_phone}
            sent={summary.whatsapp_sent}
            failed={summary.whatsapp_failed}
          />
        </section>
      ) : null}
    </div>
  );
}

function SmsWhatsappNarrative({
  channel,
  attempted,
  skippedNoPhone,
  sent,
  failed,
}: {
  channel: "SMS" | "WhatsApp";
  attempted: number;
  skippedNoPhone: number;
  sent: number;
  failed: number;
}) {
  const totalConsidered = attempted + skippedNoPhone;
  const messagesLower = channel === "SMS" ? "text messages" : "WhatsApp messages";

  return (
    <div className="mt-1 space-y-2">
      {totalConsidered > 0 ? (
        <p>
          We tried to send {messagesLower} to {totalConsidered}{" "}
          {plural(totalConsidered, "user", "users")}.
        </p>
      ) : (
        <p>No users were eligible for {channel} delivery in this send.</p>
      )}
      {sent > 0 ? <p>{messageSentPhrase(sent)}</p> : null}
      {failed > 0 ? <p>{messageFailedPhrase(failed)}</p> : null}
      {skippedNoPhone > 0 ? <p>{usersSkippedNoPhonePhrase(skippedNoPhone)}</p> : null}
    </div>
  );
}
