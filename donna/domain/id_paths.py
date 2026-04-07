import fnmatch
import re
from functools import lru_cache, total_ordering
from typing import Any, Generic, Self, Sequence, TypeVar

from pydantic_core import PydanticCustomError, core_schema

from donna.core.errors import ErrorsList
from donna.core.result import Err, Ok, Result
from donna.domain import errors as domain_errors


def _match_pattern_parts(  # noqa: CCR001
    pattern_parts: Sequence["IdPathSegmentMatcher"], value_parts: Sequence[str]
) -> bool:
    def match_at(p_index: int, v_index: int) -> bool:  # noqa: CCR001
        while True:
            if p_index >= len(pattern_parts):
                return v_index >= len(value_parts)

            matcher = pattern_parts[p_index]

            if matcher.is_recursive():
                for next_index in range(v_index, len(value_parts) + 1):
                    if match_at(p_index + 1, next_index):
                        return True
                return False

            if v_index >= len(value_parts):
                return False

            if not matcher.matches_segment(value_parts[v_index]):
                return False

            p_index += 1
            v_index += 1

    return match_at(0, 0)


def _match_pattern_prefix(pattern_parts: Sequence["IdPathSegmentMatcher"], prefix_parts: Sequence[str]) -> bool:
    @lru_cache(maxsize=None)
    def match_at(p_index: int, v_index: int) -> bool:  # noqa: CCR001
        if v_index >= len(prefix_parts):
            return True

        if p_index >= len(pattern_parts):
            return False

        matcher = pattern_parts[p_index]

        if matcher.is_recursive():
            return match_at(p_index + 1, v_index) or match_at(p_index, v_index + 1)

        if matcher.matches_segment(prefix_parts[v_index]):
            return match_at(p_index + 1, v_index + 1)

        return False

    return match_at(0, 0)


def _stringify_value(value: Any) -> str:
    if isinstance(value, str):
        return value
    return repr(value)


def _pydantic_type_error(type_name: str, value: Any) -> PydanticCustomError:
    return PydanticCustomError(
        "type_error",
        "{type_name} must be a str, got {actual_type}",
        {"type_name": type_name, "actual_type": type(value).__name__},
    )


def _pydantic_value_error(type_name: str, value: Any) -> PydanticCustomError:
    return PydanticCustomError(
        "value_error",
        "Invalid {type_name}: {value}",
        {"type_name": type_name, "value": _stringify_value(value)},
    )


TParsed = TypeVar("TParsed")


def _invalid_format(id_type: str, value: Any) -> Result[TParsed, ErrorsList]:
    return Err([domain_errors.InvalidIdFormat(id_type=id_type, value=_stringify_value(value))])


def _invalid_pattern(id_type: str, value: Any) -> Result[TParsed, ErrorsList]:
    return Err([domain_errors.InvalidIdPattern(id_type=id_type, value=_stringify_value(value))])


class NormalizedRawIdPath(str):
    __slots__ = ()


class IdPathSegmentMatcher:
    __slots__ = ("pattern_text",)
    pattern_text: str

    def __init__(self, pattern_text: str) -> None:
        self.pattern_text = pattern_text

    def __str__(self) -> str:
        return self.pattern_text

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.pattern_text!r})"

    def __hash__(self) -> int:
        return hash((type(self), self.pattern_text))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented

        return self.pattern_text == other.pattern_text

    def matches_segment(self, value: str) -> bool:
        raise NotImplementedError

    def is_recursive(self) -> bool:
        return False


class IdPathSegmentLiteralMatcher(IdPathSegmentMatcher):
    __slots__ = ()

    def matches_segment(self, value: str) -> bool:
        return self.pattern_text == value


class IdPathSegmentSingleMatcher(IdPathSegmentMatcher):
    __slots__ = ("_regex",)
    _regex: re.Pattern[str]

    def __init__(self, pattern_text: str) -> None:
        super().__init__(pattern_text)
        self._regex = re.compile(fnmatch.translate(pattern_text))

    def matches_segment(self, value: str) -> bool:
        return self._regex.fullmatch(value) is not None


class IdPathSegmentRecursiveMatcher(IdPathSegmentMatcher):
    __slots__ = ()

    def matches_segment(self, value: str) -> bool:
        return True

    def is_recursive(self) -> bool:
        return True


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
    def validate(cls, value: str) -> bool:
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
    def normalize_raw_value(cls, value: str) -> NormalizedRawIdPath | None:
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

    def __deepcopy__(self, memo: dict[int, Any]) -> Self:
        memo[id(self)] = self
        return self

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError(f"{type(self).__name__} is immutable")

    @classmethod
    def parse(cls, text: str) -> Result[Self, ErrorsList]:
        normalized = cls.normalize_raw_value(text)
        if normalized is None:
            return _invalid_format(cls.__name__, text)

        return Ok(cls(normalized))

    @classmethod
    def _build_pydantic_schema(cls, validate_func: Any) -> core_schema.CoreSchema:
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
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: Any) -> core_schema.CoreSchema:

        def validate(v: Any) -> "IdPath":
            if isinstance(v, cls):
                return v

            if not isinstance(v, str):
                raise _pydantic_type_error(cls.__name__, v)

            normalized = cls.normalize_raw_value(v)
            if normalized is None:
                raise _pydantic_value_error(cls.__name__, v)

            return cls(normalized)

        return cls._build_pydantic_schema(validate)


TIdPath = TypeVar("TIdPath", bound="IdPath")
TIdPathPattern = TypeVar("TIdPathPattern", bound="IdPathPattern[Any]")


class IdPathPattern(tuple[IdPathSegmentMatcher, ...], Generic[TIdPath]):
    __slots__ = ()
    id_class: type[TIdPath]

    def __str__(self) -> str:
        return self.id_class.delimiter.join(str(part) for part in self)

    @classmethod
    def _parse_pattern_part(cls, part: str) -> IdPathSegmentMatcher | None:
        if part == "**":
            return IdPathSegmentRecursiveMatcher(part)

        if part == "":
            return None

        if any(char in part for char in "*?[]"):
            return IdPathSegmentSingleMatcher(part)

        if not part.isidentifier():
            return None

        return IdPathSegmentLiteralMatcher(part)

    @classmethod
    def parse(cls: type[TIdPathPattern], text: str) -> Result[TIdPathPattern, ErrorsList]:  # noqa: CCR001
        if not isinstance(text, str) or not text:
            return _invalid_pattern(cls.__name__, text)

        if not cls.id_class.delimiter:
            return _invalid_pattern(cls.__name__, text)

        if cls.id_class.prefix and text.startswith(cls.id_class.prefix):
            text = text.removeprefix(cls.id_class.prefix)

        parts = text.split(cls.id_class.delimiter)

        if any(part == "" for part in parts):
            return _invalid_pattern(cls.__name__, text)

        compiled_parts: list[IdPathSegmentMatcher] = []

        for part in parts:
            matcher = cls._parse_pattern_part(part)
            if matcher is None:
                return _invalid_pattern(cls.__name__, text)
            compiled_parts.append(matcher)

        return Ok(cls(compiled_parts))

    def matches(self, value: TIdPath) -> bool:
        return _match_pattern_parts(self, value.parts)

    def matches_prefix(self, prefix_parts: Sequence[str]) -> bool:
        return _match_pattern_prefix(self, prefix_parts)

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: Any) -> core_schema.CoreSchema:  # noqa: CCR001

        def validate(v: Any) -> "IdPathPattern[TIdPath]":
            if isinstance(v, cls):
                return v

            if not isinstance(v, str):
                raise _pydantic_type_error(cls.__name__, v)

            result = cls.parse(v)
            errors = result.err()
            if errors is not None:
                error = errors[0]
                raise PydanticCustomError("value_error", error.message.format(error=error))

            parsed = result.ok()
            if parsed is None:
                raise _pydantic_value_error(cls.__name__, v)

            return parsed

        str_then_validate = core_schema.no_info_after_validator_function(
            validate,
            core_schema.str_schema(),
        )

        return core_schema.json_or_python_schema(
            json_schema=str_then_validate,
            python_schema=core_schema.no_info_plain_validator_function(validate),
            serialization=core_schema.to_string_ser_schema(),
        )
