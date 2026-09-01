from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.models.enums import (
    ApplicationStatus,
    JobSource,
    WorkModel,
)
from app.schemas.application import ApplicationRead
from app.schemas.application_query import (
    ApplicationListParams,
    ApplicationListResponse,
)


def create_application_read() -> ApplicationRead:
    now = datetime.now(UTC)

    return ApplicationRead(
        id=uuid4(),
        user_id=uuid4(),
        company_id=uuid4(),
        position="Backend Engineer",
        status=ApplicationStatus.APPLIED,
        source=JobSource.LINKEDIN,
        work_model=WorkModel.HYBRID,
        location="Dublin, Ireland",
        job_url=None,
        salary_min=None,
        salary_max=None,
        currency=None,
        applied_at=now,
        notes=None,
        created_at=now,
        updated_at=now,
    )


def test_application_list_params_uses_expected_defaults() -> None:
    params = ApplicationListParams()

    assert params.status is None
    assert params.company_id is None
    assert params.work_model is None
    assert params.source is None
    assert params.search is None

    assert params.limit == 20
    assert params.offset == 0
    assert params.sort_by == "created_at"
    assert params.sort_order == "desc"


def test_application_list_params_accepts_filters_pagination_and_sorting() -> None:
    company_id = uuid4()

    params = ApplicationListParams(
        status=ApplicationStatus.INTERVIEW,
        company_id=company_id,
        work_model=WorkModel.REMOTE,
        source=JobSource.LINKEDIN,
        search="backend",
        limit=50,
        offset=100,
        sort_by="applied_at",
        sort_order="asc",
    )

    assert params.status is ApplicationStatus.INTERVIEW
    assert params.company_id == company_id
    assert params.work_model is WorkModel.REMOTE
    assert params.source is JobSource.LINKEDIN
    assert params.search == "backend"
    assert params.limit == 50
    assert params.offset == 100
    assert params.sort_by == "applied_at"
    assert params.sort_order == "asc"


def test_application_list_params_strips_search_whitespace() -> None:
    params = ApplicationListParams(
        search="  backend engineer  ",
    )

    assert params.search == "backend engineer"


def test_application_list_params_rejects_blank_search() -> None:
    with pytest.raises(ValidationError):
        ApplicationListParams(
            search="   ",
        )


def test_application_list_params_rejects_search_longer_than_200() -> None:
    with pytest.raises(ValidationError):
        ApplicationListParams(
            search="a" * 201,
        )


@pytest.mark.parametrize(
    "limit",
    [
        1,
        100,
    ],
)
def test_application_list_params_accepts_limit_boundaries(
    limit: int,
) -> None:
    params = ApplicationListParams(
        limit=limit,
    )

    assert params.limit == limit


@pytest.mark.parametrize(
    "limit",
    [
        0,
        101,
    ],
)
def test_application_list_params_rejects_invalid_limit(
    limit: int,
) -> None:
    with pytest.raises(ValidationError):
        ApplicationListParams(
            limit=limit,
        )


def test_application_list_params_rejects_negative_offset() -> None:
    with pytest.raises(ValidationError):
        ApplicationListParams(
            offset=-1,
        )


def test_application_list_params_rejects_invalid_sort_by() -> None:
    with pytest.raises(ValidationError):
        ApplicationListParams(
            sort_by="salary_min",  # type: ignore[arg-type]
        )


def test_application_list_params_rejects_invalid_sort_order() -> None:
    with pytest.raises(ValidationError):
        ApplicationListParams(
            sort_order="random",  # type: ignore[arg-type]
        )


def test_application_list_params_rejects_invalid_status() -> None:
    with pytest.raises(ValidationError):
        ApplicationListParams(
            status="unknown",  # type: ignore[arg-type]
        )


def test_application_list_params_rejects_invalid_work_model() -> None:
    with pytest.raises(ValidationError):
        ApplicationListParams(
            work_model="everywhere",  # type: ignore[arg-type]
        )


def test_application_list_params_rejects_invalid_source() -> None:
    with pytest.raises(ValidationError):
        ApplicationListParams(
            source="facebook",  # type: ignore[arg-type]
        )


def test_application_list_response_accepts_valid_page() -> None:
    application = create_application_read()

    response = ApplicationListResponse(
        items=[application],
        total=37,
        limit=20,
        offset=20,
    )

    assert response.items == [application]
    assert response.total == 37
    assert response.limit == 20
    assert response.offset == 20


def test_application_list_response_rejects_negative_total() -> None:
    with pytest.raises(ValidationError):
        ApplicationListResponse(
            items=[],
            total=-1,
            limit=20,
            offset=0,
        )


def test_application_list_response_rejects_invalid_limit() -> None:
    with pytest.raises(ValidationError):
        ApplicationListResponse(
            items=[],
            total=0,
            limit=0,
            offset=0,
        )


def test_application_list_response_rejects_negative_offset() -> None:
    with pytest.raises(ValidationError):
        ApplicationListResponse(
            items=[],
            total=0,
            limit=20,
            offset=-1,
        )
