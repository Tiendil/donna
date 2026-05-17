import pydantic
import pytest

from donna.core.entities import BaseEntity
from donna.domain import errors
from donna.domain.internal_ids import ActionRequestId, InternalId, TaskId, WorkUnitId


class _InternalIdEntity(BaseEntity):
    internal_id: InternalId


class TestInternalId:
    def test_build__creates_crc_protected_identifier(self) -> None:
        identifier = InternalId.build("WU", 0)

        assert identifier == InternalId("WU-0-a")
        assert identifier.short == "0"
        assert InternalId.validate(identifier)

    @pytest.mark.parametrize(
        "value",
        [
            "WU-0-b",
            "WU-zero-a",
            "WU",
            "",
            None,
        ],
    )
    def test_validate__rejects_invalid_identifier(self, value: object) -> None:
        assert not InternalId.validate(value)

    def test_init__raises_internal_error_for_invalid_value(self) -> None:
        with pytest.raises(errors.InvalidInternalId):
            InternalId("WU-0-b")

    def test_pydantic_validation__accepts_internal_id_value(self) -> None:
        entity = _InternalIdEntity(internal_id="WU-0-a")

        assert entity.internal_id == InternalId("WU-0-a")
        assert entity.model_dump_json() == '{"internal_id":"WU-0-a"}'

    def test_pydantic_validation__rejects_invalid_internal_id_value(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            _InternalIdEntity(internal_id="WU-0-b")

        with pytest.raises(pydantic.ValidationError):
            _InternalIdEntity(internal_id=123)


class TestWorkUnitId:
    def test_inherits_internal_id_behavior(self) -> None:
        identifier = WorkUnitId.build("WU", 1)

        assert identifier == WorkUnitId("WU-1-b")
        assert WorkUnitId.validate(identifier)


class TestActionRequestId:
    def test_inherits_internal_id_behavior(self) -> None:
        identifier = ActionRequestId.build("AR", 1)

        assert identifier == ActionRequestId("AR-1-b")
        assert ActionRequestId.validate(identifier)


class TestTaskId:
    def test_inherits_internal_id_behavior(self) -> None:
        identifier = TaskId.build("T", 1)

        assert identifier == TaskId("T-1-b")
        assert TaskId.validate(identifier)
