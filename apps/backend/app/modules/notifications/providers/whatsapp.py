from __future__ import annotations

from app.modules.notifications.providers.base import WhatsAppDeliveryResult


async def send_whatsapp_stub(*, to_e164: str, body: str) -> WhatsAppDeliveryResult:
    """Placeholder for a future WhatsApp Business API provider."""
    _ = (to_e164, body)
    return WhatsAppDeliveryResult(
        ok=False,
        error_message="WhatsApp provider not implemented",
    )
