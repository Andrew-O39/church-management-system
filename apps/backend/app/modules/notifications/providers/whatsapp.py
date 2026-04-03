from __future__ import annotations

import logging

import httpx

from app.core.settings import settings
from app.modules.notifications.providers.base import WhatsAppDeliveryResult

logger = logging.getLogger(__name__)


def _whatsapp_address(raw: str) -> str:
    s = raw.strip()
    if s.lower().startswith("whatsapp:"):
        return s
    if s.startswith("+"):
        return f"whatsapp:{s}"
    return f"whatsapp:+{s}"


async def send_whatsapp_twilio(*, to_e164: str, body: str) -> WhatsAppDeliveryResult:
    """Send a WhatsApp message via Twilio (same Messages API as SMS, whatsapp: addresses).

    Twilio WhatsApp supports session messages to opted-in users; template messages are required
    for some outbound-initiated cases. This path sends a **session-style** body suitable for
    sandbox and ongoing conversations. If Twilio rejects the request (e.g. template required),
    the error text is stored on the delivery attempt.
    """
    provider = (settings.WHATSAPP_PROVIDER or "").strip().lower()
    sid = settings.WHATSAPP_ACCOUNT_SID or settings.SMS_ACCOUNT_SID
    token = settings.WHATSAPP_AUTH_TOKEN or settings.SMS_AUTH_TOKEN
    from_raw = settings.WHATSAPP_FROM_NUMBER

    if provider not in ("twilio", ""):
        return WhatsAppDeliveryResult(
            ok=False,
            error_message=f"Unsupported WHATSAPP_PROVIDER: {settings.WHATSAPP_PROVIDER!r}",
        )

    if not sid or not token or not from_raw:
        return WhatsAppDeliveryResult(
            ok=False,
            error_message=(
                "WhatsApp provider not configured (set WHATSAPP_PROVIDER=twilio, "
                "WHATSAPP_FROM_NUMBER, and WHATSAPP_ACCOUNT_SID / WHATSAPP_AUTH_TOKEN "
                "or reuse SMS_ACCOUNT_SID / SMS_AUTH_TOKEN)"
            ),
        )

    from_addr = _whatsapp_address(from_raw)
    to_addr = _whatsapp_address(to_e164)

    url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                data={"To": to_addr, "From": from_addr, "Body": body},
                auth=(sid, token),
                timeout=30.0,
            )
    except httpx.HTTPError as exc:
        logger.exception("WhatsApp HTTP error")
        return WhatsAppDeliveryResult(ok=False, error_message=str(exc)[:500])

    if response.status_code >= 400:
        return WhatsAppDeliveryResult(
            ok=False,
            error_message=response.text[:500] or f"HTTP {response.status_code}",
        )

    try:
        payload = response.json()
    except ValueError:
        return WhatsAppDeliveryResult(ok=True, provider_message_id=None)

    return WhatsAppDeliveryResult(ok=True, provider_message_id=payload.get("sid"))
