from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class RegistrySavedFilterCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    filters: dict[str, str] = Field(default_factory=dict)


class RegistrySavedFilterPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    filters: dict[str, str] | None = None

    @model_validator(mode="after")
    def require_name_or_filters(self) -> RegistrySavedFilterPatch:
        if self.name is None and self.filters is None:
            raise ValueError("Provide at least one of name or filters")
        return self


class RegistrySavedFilterOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    filters: dict[str, str]
    created_at: datetime
    updated_at: datetime
