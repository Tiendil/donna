import pydantic
import pytest

from donna.core.entities import BaseEntity
from donna.domain import errors
from donna.domain.ids import Identifier, SectionId


class _IdentifierEntity(BaseEntity):
    identifier: Identifier


class _SectionEntity(BaseEntity):
    section_id: SectionId


class TestIdentifier:
    def test_validate__accepts_python_identifier(self) -> None:
        assert Identifier.validate("valid_name")

    @pytest.mark.parametrize("value", ["", "1invalid", "not-valid", None])
    def test_validate__rejects_non_identifier(self, value: object) -> None:
        assert not Identifier.validate(value)

    def test_init__raises_internal_error_for_invalid_value(self) -> None:
        with pytest.raises(errors.InvalidIdentifier):
            Identifier("not-valid")

    def test_parse__returns_identifier(self) -> None:
        result = Identifier.parse("valid_name")

        assert result.is_ok()
        assert result.unwrap() == Identifier("valid_name")

    def test_parse__returns_environment_error_for_invalid_format(self) -> None:
        result = Identifier.parse("not-valid")

        assert result.is_err()
        error = result.unwrap_err()[0]
        assert isinstance(error, errors.InvalidIdFormat)
        assert error.code == "donna.domain.invalid_id_format"
        assert error.id_type == "Identifier"
        assert error.value == "not-valid"

    def test_pydantic_validation__accepts_identifier_value(self) -> None:
        entity = _IdentifierEntity(identifier="valid_name")

        assert entity.identifier == Identifier("valid_name")
        assert entity.model_dump_json() == '{"identifier":"valid_name"}'

    def test_pydantic_validation__rejects_invalid_identifier_value(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            _IdentifierEntity(identifier="not-valid")

        with pytest.raises(pydantic.ValidationError):
            _IdentifierEntity(identifier=123)


class TestSectionId:
    @pytest.mark.parametrize("value", ["section", "section-1", "section.name", "section_name"])
    def test_validate__accepts_artifact_slug_part(self, value: str) -> None:
        assert SectionId.validate(value)

    @pytest.mark.parametrize("value", ["", "---", "...", "section/id", "section id", None])
    def test_validate__rejects_invalid_artifact_slug_part(self, value: object) -> None:
        assert not SectionId.validate(value)

    def test_parse__returns_section_id(self) -> None:
        result = SectionId.parse("section-1")

        assert result.is_ok()
        assert result.unwrap() == SectionId("section-1")

    def test_parse__returns_environment_error_for_invalid_format(self) -> None:
        result = SectionId.parse("---")

        assert result.is_err()
        error = result.unwrap_err()[0]
        assert isinstance(error, errors.InvalidIdFormat)
        assert error.code == "donna.domain.invalid_id_format"
        assert error.id_type == "SectionId"
        assert error.value == "---"

    def test_pydantic_validation__accepts_section_id_value(self) -> None:
        entity = _SectionEntity(section_id="section-1")

        assert entity.section_id == SectionId("section-1")
        assert entity.model_dump_json() == '{"section_id":"section-1"}'

    def test_pydantic_validation__rejects_invalid_section_id_value(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            _SectionEntity(section_id="---")

        with pytest.raises(pydantic.ValidationError):
            _SectionEntity(section_id=123)
