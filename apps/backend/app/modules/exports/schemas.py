from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class PrintExportPayload(BaseModel):
    """Structured data for browser print / Save as PDF (no server-side PDF engine)."""

    title: str
    subtitle: str | None = None
    columns: list[str]
    rows: list[list[str | None]]
    generated_at: datetime = Field(description="UTC timestamp when the export was built.")
    church_name: str | None = Field(
        default=None,
        description="Organization name from Church Profile (singleton), if configured.",
    )
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    filters_summary: str | None = Field(
        default=None,
        description="Human-readable summary of active export filters, if any.",
    )
