import copy
from typing import Any, cast

import pydantic
import pytest

from donna.core.entities import BaseEntity
from donna.domain import errors
from donna.domain.id_paths import IdPath, NormalizedRawIdPath
from donna.domain.python_path import PythonPath


class _SlashPath(IdPath):
    __slots__ = ()
    prefix = "$/"
    delimiter = "/"
    min_parts = 2


class _PathEntity(BaseEntity):
    path: PythonPath


class TestIdPath:
    def test_normalize_raw_value__removes_prefix_and_validates_parts(self) -> None:
        assert _SlashPath.normalize_raw_value("$/alpha/beta") == NormalizedRawIdPath("alpha/beta")
        assert _SlashPath.normalize_raw_value("alpha/beta") == NormalizedRawIdPath("alpha/beta")
        assert _SlashPath.normalize_raw_value("$/alpha") is None
        assert _SlashPath.normalize_raw_value("$/alpha//beta") is None
        assert _SlashPath.normalize_raw_value("$/alpha/not-valid") is None

    def test_parse__returns_normalized_path(self) -> None:
        result = _SlashPath.parse("$/alpha/beta")

        assert result.is_ok()
        assert result.unwrap() == _SlashPath(NormalizedRawIdPath("alpha/beta"))

    def test_parse__returns_environment_error_for_invalid_format(self) -> None:
        result = _SlashPath.parse("$/alpha")

        assert result.is_err()
        error = result.unwrap_err()[0]
        assert isinstance(error, errors.InvalidIdFormat)
        assert error.code == "donna.domain.invalid_id_format"
        assert error.id_type == "_SlashPath"
        assert error.value == "$/alpha"

    def test_init__raises_internal_error_for_invalid_normalized_value(self) -> None:
        with pytest.raises(errors.InvalidIdPath):
            _SlashPath(NormalizedRawIdPath("alpha"))

    def test_string_representations__use_prefix_and_raw_value(self) -> None:
        path = _SlashPath(NormalizedRawIdPath("alpha/beta"))

        assert path.raw_value == "alpha/beta"
        assert str(path) == "$/alpha/beta"
        assert repr(path) == "_SlashPath('alpha/beta')"

    def test_equality_hashing_and_ordering__are_type_specific_and_part_based(self) -> None:
        first = _SlashPath(NormalizedRawIdPath("alpha/beta"))
        second = _SlashPath(NormalizedRawIdPath("alpha/gamma"))

        assert first == _SlashPath(NormalizedRawIdPath("alpha/beta"))
        assert first != PythonPath(NormalizedRawIdPath("alpha.beta"))
        assert sorted([second, first]) == [first, second]
        assert {first, _SlashPath(NormalizedRawIdPath("alpha/beta"))} == {first}

    def test_copy__preserves_value_semantics(self) -> None:
        path = _SlashPath(NormalizedRawIdPath("alpha/beta"))

        assert copy.copy(path) == path
        assert copy.deepcopy(path) == path

    def test_setattr__rejects_mutation(self) -> None:
        path = _SlashPath(NormalizedRawIdPath("alpha/beta"))

        with pytest.raises(AttributeError):
            path.parts = ("changed",)


class TestPythonPath:
    def test_parse__accepts_dotted_python_path(self) -> None:
        result = PythonPath.parse("donna.domain.ids")

        assert result.is_ok()
        assert result.unwrap().parts == ("donna", "domain", "ids")

    def test_parse__rejects_empty_and_malformed_parts(self) -> None:
        assert PythonPath.parse("").is_err()
        assert PythonPath.parse("donna..ids").is_err()
        assert PythonPath.parse("donna.domain.1ids").is_err()

    def test_pydantic_validation__accepts_and_serializes_python_path(self) -> None:
        entity = _PathEntity.model_validate({"path": "donna.domain.ids"})

        assert entity.path == PythonPath(NormalizedRawIdPath("donna.domain.ids"))
        assert entity.model_dump() == {"path": PythonPath(NormalizedRawIdPath("donna.domain.ids"))}
        assert entity.model_dump_json() == '{"path":"donna.domain.ids"}'

    def test_pydantic_validation__rejects_invalid_python_value(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            _PathEntity.model_validate({"path": "donna..ids"})

        with pytest.raises(pydantic.ValidationError):
            _PathEntity.model_validate({"path": cast(Any, 123)})
