from __future__ import annotations

import logging

import httpx

from app.core.settings import settings
from app.modules.notifications.providers.base import SMSDeliveryResult

logger = logging.getLogger(__name__)


async def send_sms_twilio(*, to_e164: str, body: str) -> SMSDeliveryResult:
    """Send SMS via Twilio REST API. Safe no-op style failure when not configured."""
    sid = settings.SMS_ACCOUNT_SID
    token = settings.SMS_AUTH_TOKEN
    from_num = settings.SMS_FROM_NUMBER
    provider = (settings.SMS_PROVIDER or "").strip().lower()

    if provider not in ("twilio", ""):
        return SMSDeliveryResult(
            ok=False,
            error_message=f"Unsupported SMS_PROVIDER: {settings.SMS_PROVIDER!r}",
        )

    if not sid or not token or not from_num:
        return SMSDeliveryResult(
            ok=False,
            error_message="SMS provider not configured (set SMS_PROVIDER=twilio and SMS_ACCOUNT_SID, SMS_AUTH_TOKEN, SMS_FROM_NUMBER)",
        )

    url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                data={"To": to_e164, "From": from_num, "Body": body},
                auth=(sid, token),
                timeout=30.0,
            )
    except httpx.HTTPError as exc:
        logger.exception("SMS HTTP error")
        return SMSDeliveryResult(ok=False, error_message=str(exc)[:500])

    if response.status_code >= 400:
        return SMSDeliveryResult(
            ok=False,
            error_message=response.text[:500] or f"HTTP {response.status_code}",
        )

    try:
        payload = response.json()
    except ValueError:
        return SMSDeliveryResult(ok=True, provider_message_id=None)

    return SMSDeliveryResult(ok=True, provider_message_id=payload.get("sid"))
