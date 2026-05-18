from collections.abc import Callable
from functools import total_ordering
from typing import Self, Sequence, TypeVar

from pydantic_core import PydanticCustomError, core_schema

from donna.core.errors import ErrorsList
from donna.core.result import Err, Ok, Result
from donna.domain import errors as domain_errors


def _stringify_value(value: object) -> str:
    if isinstance(value, str):
        return value
    return repr(value)


def _pydantic_type_error(type_name: str, value: object) -> PydanticCustomError:
    return PydanticCustomError(
        "type_error",
        "{type_name} must be a str, got {actual_type}",
        {"type_name": type_name, "actual_type": type(value).__name__},
    )


def _pydantic_value_error(type_name: str, value: object) -> PydanticCustomError:
    return PydanticCustomError(
        "value_error",
        "Invalid {type_name}: {value}",
        {"type_name": type_name, "value": _stringify_value(value)},
    )


TParsed = TypeVar("TParsed")


def _invalid_format(id_type: str, value: object) -> Result[TParsed, ErrorsList]:
    return Err([domain_errors.InvalidIdFormat(id_type=id_type, value=_stringify_value(value))])


class NormalizedRawIdPath(str):
    __slots__ = ()


@total_ordering
class IdPath:
    __slots__ = ("parts",)
    prefix: str = ""
    delimiter: str = ""
    min_parts: int = 1
    validate_json: bool = False
    parts: tuple[str, ...]

    def __init__(self, value: NormalizedRawIdPath) -> None:
        cls = type(self)

        if not cls.validate(value):
            raise domain_errors.InvalidIdPath(id_type=cls.__name__, value=value)

        object.__setattr__(self, "parts", tuple(cls._split(value)))

    @classmethod
    def _split(cls, value: str) -> list[str]:
        return value.split(cls.delimiter)

    @classmethod
    def _validate_parts(cls, parts: Sequence[str]) -> bool:
        return all(part.isidentifier() for part in parts)

    @classmethod
    def validate(cls, value: object) -> bool:
        if not isinstance(value, str) or not value:
            return False

        if not cls.delimiter:
            return False

        parts = cls._split(value)

        if any(part == "" for part in parts):
            return False

        if len(parts) < cls.min_parts:
            return False

        return cls._validate_parts(parts)

    @property
    def raw_value(self) -> str:
        return self.delimiter.join(self.parts)

    @classmethod
    def normalize_raw_value(cls, value: object) -> NormalizedRawIdPath | None:
        if not isinstance(value, str) or not value:
            return None

        normalized = value
        if cls.prefix and normalized.startswith(cls.prefix):
            normalized = normalized.removeprefix(cls.prefix)

        if not cls.validate(normalized):
            return None

        return NormalizedRawIdPath(normalized)

    def __str__(self) -> str:
        return f"{self.prefix}{self.raw_value}"

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.raw_value!r})"

    def __hash__(self) -> int:
        return hash((type(self), self.parts))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented

        return self.parts == other.parts

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented

        return self.parts < other.parts

    def __copy__(self) -> Self:
        return self

    def __deepcopy__(self, memo: dict[int, object]) -> Self:
        memo[id(self)] = self
        return self

    def __setattr__(self, name: str, value: object) -> None:
        raise AttributeError(f"{type(self).__name__} is immutable")

    @classmethod
    def parse(cls, text: object) -> Result[Self, ErrorsList]:
        normalized = cls.normalize_raw_value(text)
        if normalized is None:
            return _invalid_format(cls.__name__, text)

        return Ok(cls(normalized))

    @classmethod
    def _build_pydantic_schema(cls, validate_func: Callable[[object], "IdPath"]) -> core_schema.CoreSchema:
        str_then_validate = core_schema.no_info_after_validator_function(
            validate_func,
            core_schema.str_schema(),
        )

        json_schema = str_then_validate if cls.validate_json else core_schema.str_schema()

        return core_schema.json_or_python_schema(
            json_schema=json_schema,
            python_schema=core_schema.no_info_plain_validator_function(validate_func),
            serialization=core_schema.to_string_ser_schema(),
        )

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: object, handler: object) -> core_schema.CoreSchema:

        def validate(v: object) -> "IdPath":
            if isinstance(v, cls):
                return v

            if not isinstance(v, str):
                raise _pydantic_type_error(cls.__name__, v)

            normalized = cls.normalize_raw_value(v)
            if normalized is None:
                raise _pydantic_value_error(cls.__name__, v)

            return cls(normalized)

        return cls._build_pydantic_schema(validate)
