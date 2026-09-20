import re
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictStr, field_validator

FIELDS = ("first_name", "last_name", "job_title", "company", "location", "phone", "email")
Text = Annotated[StrictStr, Field(max_length=500)]
EMPTY_VALUES = {"", "n/a", "na", "none", "null", "unknown", "not available", "not visible"}


class Lead(BaseModel):
    model_config = ConfigDict(extra="forbid")
    first_name: Text | None = None
    last_name: Text | None = None
    job_title: Text | None = None
    company: Text | None = None
    location: Text | None = None
    phone: Text | None = None
    email: Text | None = None

    @field_validator(*FIELDS, mode="before")
    @classmethod
    def normalize_empty(cls, value):
        if isinstance(value, str):
            value = value.strip()
            if value.lower() in EMPTY_VALUES:
                return None
            value = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\ud800-\udfff\ufffe\uffff]", "", value)
            if not value:
                return None
        return value


class CardResult(BaseModel):
    index: int
    source_filename: str
    status: Literal["success", "error"]
    lead: Lead | None = None
    error: str | None = None
    warnings: list[str] = Field(default_factory=list)
    processing_time_ms: float


class JobView(BaseModel):
    job_id: str
    status: Literal["queued", "processing", "completed", "failed"]
    total: int
    processed: int
    successful: int
    failed: int
    processing_time_seconds: float
    leads: list[CardResult]
    error: str | None = None


class ExportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    leads: list[Lead] = Field(min_length=1, max_length=20)
