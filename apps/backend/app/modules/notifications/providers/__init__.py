"""External messaging provider adapters (SMS, WhatsApp stub)."""

from app.modules.notifications.providers import sms, whatsapp
from app.modules.notifications.providers.base import SMSDeliveryResult, SMSProvider

__all__ = ["SMSDeliveryResult", "SMSProvider", "sms", "whatsapp"]
