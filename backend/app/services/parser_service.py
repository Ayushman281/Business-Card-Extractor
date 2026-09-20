"""Recover JSON without guessing or repairing its field values."""
import json
import re

from pydantic import ValidationError

from app.models.lead import FIELDS, Lead


class ExtractionError(Exception):
    """Safe, user-facing extraction failure."""


def parse_lead(raw: str) -> Lead:
    if not raw or len(raw) > 20_000:
        raise ExtractionError("The model did not return a usable response. Try a clearer image.")
    candidate = raw.strip()
    if candidate.startswith("```"):
        candidate = re.sub(r"^```(?:json)?\s*", "", candidate, flags=re.IGNORECASE)
        candidate = re.sub(r"\s*```$", "", candidate)
    try:
        value = json.loads(candidate)
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        value = None
        for match in re.finditer(r"\{", candidate):
            try:
                found, _ = decoder.raw_decode(candidate[match.start():])
            except json.JSONDecodeError:
                continue
            if isinstance(found, dict) and set(found).intersection(FIELDS):
                value = found
                break
    if not isinstance(value, dict) or not set(value).intersection(FIELDS):
        raise ExtractionError("The model returned invalid lead JSON. Try a clearer image.")
    try:
        return Lead.model_validate(value)
    except ValidationError:
        raise ExtractionError("The model returned fields in an unexpected format. Please retry.") from None


def lead_warnings(lead: Lead) -> list[str]:
    warnings = []
    if not any(lead.model_dump().values()):
        warnings.append("No readable lead information was found. Review the image.")
    if lead.email and not all(
        re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", part.strip())
        for part in lead.email.split(";")
    ):
        warnings.append("Please check the email address; its format looks unusual.")
    if lead.phone and sum(c.isdigit() for c in lead.phone) < 5:
        warnings.append("Please check the phone number; it contains few digits.")
    return warnings
