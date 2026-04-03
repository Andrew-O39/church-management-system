from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class SMSDeliveryResult:
    ok: bool
    provider_message_id: str | None = None
    error_message: str | None = None


@runtime_checkable
class SMSProvider(Protocol):
    async def send_sms(self, *, to_e164: str, body: str) -> SMSDeliveryResult: ...


@dataclass(frozen=True)
class WhatsAppDeliveryResult:
    ok: bool
    provider_message_id: str | None = None
    error_message: str | None = None


@runtime_checkable
class WhatsAppProvider(Protocol):
    async def send_whatsapp(self, *, to_e164: str, body: str) -> WhatsAppDeliveryResult: ...
