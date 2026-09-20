import pytest
from pydantic import ValidationError

from app.models.lead import Lead
from app.services.parser_service import ExtractionError, lead_warnings, parse_lead


@pytest.mark.parametrize("value", ["", "  ", "N/A", "unknown", "null", None])
def test_missing_values_are_null(value):
    assert Lead(first_name=value).first_name is None


def test_partial_lead_and_international_phone():
    lead = Lead(first_name="  Ana  ", phone="+91 (22) 2345-6789")
    assert lead.first_name == "Ana"
    assert lead.last_name is None
    assert lead.phone == "+91 (22) 2345-6789"


@pytest.mark.parametrize("value", [123, True, ["Ana"], {"name": "Ana"}])
def test_schema_rejects_wrong_types(value):
    with pytest.raises(ValidationError):
        Lead(first_name=value)


@pytest.mark.parametrize("raw", [
    '{"first_name":"Ana","last_name":null}',
    '```json\n{"first_name":"Ana"}\n```',
    'Here is the result: {"first_name":"Ana"} Done.',
    'An invalid {example} followed by {"first_name":"Ana"}',
])
def test_parser_accepts_wrapped_objects(raw):
    assert parse_lead(raw).first_name == "Ana"


@pytest.mark.parametrize("raw", ["", "not JSON", "{", "{}", "[]", '{"first_name": 5}', '{"first_name":"A","unexpected":"x"}'])
def test_parser_rejects_bad_responses(raw):
    with pytest.raises(ExtractionError):
        parse_lead(raw)


def test_null_model_result_warns_without_invention():
    lead = parse_lead('{"first_name": null}')
    assert all(value is None for value in lead.model_dump().values())
    assert lead_warnings(lead)


def test_email_validation_preserves_suspect_value_for_review():
    lead = Lead(email="example.com")
    assert lead.email == "example.com"
    assert lead_warnings(lead)
    assert not lead_warnings(Lead(email="a@example.com; b@example.org"))


def test_output_controls_are_removed():
    assert Lead(company="Acme\\x01").company == "Acme\\x01"
    assert Lead(company="Acme\x01").company == "Acme"
