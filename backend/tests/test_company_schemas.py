import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.schemas.company import CompanyCreate, CompanyRead, CompanyUpdate


def test_company_create_with_valid_data() -> None:
    company = CompanyCreate(
        name="Stripe",
        website="https://stripe.com",
        industry="Fintech",
        location="Dublin, Ireland",
    )

    assert company.name == "Stripe"
    assert company.website == "https://stripe.com"
    assert company.industry == "Fintech"
    assert company.location == "Dublin, Ireland"


def test_company_create_rejects_empty_name() -> None:
    with pytest.raises(ValidationError):
        CompanyCreate(name="")


def test_company_update_contains_only_provided_fields() -> None:
    update = CompanyUpdate(location="Cork, Ireland")

    assert update.model_dump(exclude_unset=True) == {
        "location": "Cork, Ireland",
    }


def test_company_update_distinguishes_missing_from_null() -> None:
    missing = CompanyUpdate()
    explicit_null = CompanyUpdate(website=None)

    assert missing.model_dump(exclude_unset=True) == {}
    assert explicit_null.model_dump(exclude_unset=True) == {
        "website": None,
    }


def test_company_read_from_attributes() -> None:
    company_id = uuid.uuid4()
    user_id = uuid.uuid4()
    now = datetime.now(UTC)

    company = SimpleNamespace(
        id=company_id,
        user_id=user_id,
        name="Stripe",
        website="https://stripe.com",
        industry="Fintech",
        location="Dublin, Ireland",
        created_at=now,
        updated_at=now,
    )

    result = CompanyRead.model_validate(company)

    assert result.id == company_id
    assert result.user_id == user_id
    assert result.name == "Stripe"
    assert result.created_at == now
    assert result.updated_at == now


def test_company_create_rejects_whitespace_only_name() -> None:
    with pytest.raises(ValidationError):
        CompanyCreate(name="   ")


def test_company_create_strips_surrounding_whitespace() -> None:
    company = CompanyCreate(
        name="  Stripe  ",
        industry="  Fintech  ",
    )

    assert company.name == "Stripe"
    assert company.industry == "Fintech"
