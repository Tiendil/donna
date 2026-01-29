from typing import Any, Generic, Sequence, TypeVar

from pydantic_core import PydanticCustomError, core_schema

from donna.core.errors import ErrorsList
from donna.core.result import Err, Ok, Result
from donna.domain import errors as domain_errors


def _id_crc(number: int) -> str:
    """Translates int into a compact string representation with a-zA-Z0-9 characters."""
    charset = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    base = len(charset)

    if number == 0:
        return charset[0]

    chars = []
    while number > 0:
        number, rem = divmod(number, base)
        chars.append(charset[rem])

    chars.reverse()
    return "".join(chars)


def _match_pattern_parts(pattern_parts: Sequence[str], value_parts: Sequence[str]) -> bool:  # noqa: CCR001
    def match_at(p_index: int, v_index: int) -> bool:  # noqa: CCR001
        while True:
            if p_index >= len(pattern_parts):
                return v_index >= len(value_parts)

            token = pattern_parts[p_index]

            if token == "**":  # noqa: S105
                for next_index in range(v_index, len(value_parts) + 1):
                    if match_at(p_index + 1, next_index):
                        return True
                return False

            if v_index >= len(value_parts):
                return False

            if token != "*" and token != value_parts[v_index]:  # noqa: S105
                return False

            p_index += 1
            v_index += 1

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


class InternalId(str):
    __slots__ = ()

    def __new__(cls, value: str) -> "InternalId":
        if not cls.validate(value):
            raise domain_errors.InvalidInternalId(value=value)

        return super().__new__(cls, value)

    @classmethod
    def build(cls, prefix: str, value: int) -> "InternalId":
        return cls(f"{prefix}-{value}-{_id_crc(value)}")

    @classmethod
    def validate(cls, id: str) -> bool:
        if not isinstance(id, str):
            return False

        try:
            _prefix, value, crc = id.rsplit("-", maxsplit=2)
        except ValueError:
            return False

        try:
            expected_crc = _id_crc(int(value))
        except ValueError:
            return False

        return crc == expected_crc

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: Any) -> core_schema.CoreSchema:  # noqa: CCR001

        def validate(v: Any) -> "InternalId":
            if isinstance(v, cls):
                return v

            if not isinstance(v, str):
                raise _pydantic_type_error(cls.__name__, v)

            if not cls.validate(v):
                raise _pydantic_value_error(cls.__name__, v)

            return cls(v)

        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.no_info_plain_validator_function(validate),
            serialization=core_schema.to_string_ser_schema(),
        )


class WorkUnitId(InternalId):
    __slots__ = ()


class ActionRequestId(InternalId):
    __slots__ = ()


class TaskId(InternalId):
    __slots__ = ()


class Identifier(str):
    __slots__ = ()

    def __new__(cls, value: str) -> "Identifier":
        if not cls.validate(value):
            raise domain_errors.InvalidIdentifier(value=value)

        return super().__new__(cls, value)

    @classmethod
    def validate(cls, value: str) -> bool:
        if not isinstance(value, str):
            return False
        return value.isidentifier()

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: Any) -> core_schema.CoreSchema:  # noqa: CCR001

        def validate(v: Any) -> "Identifier":
            if isinstance(v, cls):
                return v

            if not isinstance(v, str):
                raise _pydantic_type_error(cls.__name__, v)

            if not cls.validate(v):
                raise _pydantic_value_error(cls.__name__, v)

            return cls(v)

        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.no_info_plain_validator_function(validate),
            serialization=core_schema.to_string_ser_schema(),
        )


class WorldId(Identifier):
    __slots__ = ()


class IdPath(str):
    __slots__ = ()
    delimiter: str = ""
    min_parts: int = 1
    validate_json: bool = False

    def __new__(cls, value: str | tuple[str, ...] | list[str]) -> "IdPath":
        text = cls._coerce_to_text(value)

        if not cls.validate(text):
            raise domain_errors.InvalidIdPath(id_type=cls.__name__, value=text)

        return super().__new__(cls, text)

    @classmethod
    def _coerce_to_text(cls, value: str | tuple[str, ...] | list[str]) -> str:
        if isinstance(value, str):
            return value

        return cls.delimiter.join(str(part) for part in value)

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
    def parts(self) -> tuple[str, ...]:
        return tuple(self._split(str.__str__(self)))

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

            if not cls.validate(v):
                raise _pydantic_value_error(cls.__name__, v)

            return cls(v)

        return cls._build_pydantic_schema(validate)


TIdPath = TypeVar("TIdPath", bound="IdPath")
TIdPathPattern = TypeVar("TIdPathPattern", bound="IdPathPattern[Any]")


class IdPathPattern(tuple[str, ...], Generic[TIdPath]):
    __slots__ = ()
    id_class: type[TIdPath]

    def __str__(self) -> str:
        return self.id_class.delimiter.join(self)

    @classmethod
    def _validate_pattern_part(cls, part: str) -> bool:
        if part in {"*", "**"}:
            return True

        return part.isidentifier()

    @classmethod
    def parse(cls: type[TIdPathPattern], text: str) -> Result[TIdPathPattern, ErrorsList]:  # noqa: CCR001
        if not isinstance(text, str) or not text:
            return _invalid_pattern(cls.__name__, text)

        if not cls.id_class.delimiter:
            return _invalid_pattern(cls.__name__, text)

        parts = text.split(cls.id_class.delimiter)

        if any(part == "" for part in parts):
            return _invalid_pattern(cls.__name__, text)

        for part in parts:
            if not cls._validate_pattern_part(part):
                return _invalid_pattern(cls.__name__, text)

        return Ok(cls(parts))

    def matches(self, value: TIdPath) -> bool:
        return _match_pattern_parts(self, self.id_class._split(str(value)))

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


class DottedPath(IdPath):
    __slots__ = ()
    delimiter = "."


class ColonPath(IdPath):
    __slots__ = ()
    delimiter = ":"


class ArtifactId(ColonPath):
    __slots__ = ()


class PythonImportPath(DottedPath):
    __slots__ = ()

    @classmethod
    def parse(cls, text: str) -> Result["PythonImportPath", ErrorsList]:
        if not isinstance(text, str) or not text:
            return _invalid_format(cls.__name__, text)

        if not cls.validate(text):
            return _invalid_format(cls.__name__, text)

        return Ok(cls(text))


class FullArtifactId(ColonPath):
    __slots__ = ()
    min_parts = 2
    validate_json = True

    def __str__(self) -> str:
        return f"{self.world_id}{self.delimiter}{self.artifact_id}"

    @property
    def world_id(self) -> WorldId:
        return WorldId(self.parts[0])

    @property
    def artifact_id(self) -> ArtifactId:
        return ArtifactId(self.delimiter.join(self.parts[1:]))

    def to_full_local(self, local_id: "ArtifactSectionId") -> "FullArtifactSectionId":
        return FullArtifactSectionId(f"{self}:{local_id}")

    @classmethod
    def parse(cls, text: str) -> Result["FullArtifactId", ErrorsList]:
        if not isinstance(text, str) or not text:
            return _invalid_format(f"{cls.__name__} format", text)

        if not cls.delimiter:
            return _invalid_format(f"{cls.__name__} format", text)

        parts = text.split(cls.delimiter, maxsplit=1)

        if len(parts) != 2:
            return _invalid_format(f"{cls.__name__} format", text)

        world_part, artifact_part = parts

        if not WorldId.validate(world_part):
            return _invalid_format(f"{cls.__name__} format", text)

        if not ArtifactId.validate(artifact_part):
            return _invalid_format(f"{cls.__name__} format", text)

        return Ok(FullArtifactId(f"{world_part}{cls.delimiter}{artifact_part}"))


class FullArtifactIdPattern(IdPathPattern["FullArtifactId"]):
    __slots__ = ()
    id_class = FullArtifactId

    def matches_full_id(self, full_id: "FullArtifactId") -> bool:
        return self.matches(full_id)


class ArtifactSectionId(Identifier):
    __slots__ = ()

    @classmethod
    def parse(cls, text: str) -> Result["ArtifactSectionId", ErrorsList]:
        if not isinstance(text, str) or not text:
            return _invalid_format(cls.__name__, text)

        if not cls.validate(text):
            return _invalid_format(cls.__name__, text)

        return Ok(cls(text))


class FullArtifactSectionId(ColonPath):
    __slots__ = ()
    min_parts = 3
    validate_json = True

    def __str__(self) -> str:
        return f"{self.world_id}{self.delimiter}{self.artifact_id}{self.delimiter}{self.local_id}"

    @property
    def world_id(self) -> WorldId:
        return WorldId(self.parts[0])

    @property
    def artifact_id(self) -> ArtifactId:
        return ArtifactId(self.delimiter.join(self.parts[1:-1]))

    @property
    def full_artifact_id(self) -> FullArtifactId:
        return FullArtifactId(f"{self.world_id}{self.delimiter}{self.artifact_id}")

    @property
    def local_id(self) -> ArtifactSectionId:
        return ArtifactSectionId(self.parts[-1])

    @classmethod
    def parse(cls, text: str) -> Result["FullArtifactSectionId", ErrorsList]:  # noqa: CCR001
        if not isinstance(text, str) or not text:
            return _invalid_format(f"{cls.__name__} format", text)

        if not cls.delimiter:
            return _invalid_format(f"{cls.__name__} format", text)

        try:
            artifact_part, local_part = text.rsplit(cls.delimiter, maxsplit=1)
        except ValueError:
            return _invalid_format(f"{cls.__name__} format", text)

        full_artifact_id_result = FullArtifactId.parse(artifact_part)
        errors = full_artifact_id_result.err()
        if errors is not None:
            return Err(errors)

        full_artifact_id = full_artifact_id_result.ok()
        if full_artifact_id is None:
            return _invalid_format(f"{cls.__name__} format", text)

        local_id_result = ArtifactSectionId.parse(local_part)
        local_errors = local_id_result.err()
        if local_errors is not None:
            return Err(local_errors)

        local_id = local_id_result.ok()
        if local_id is None:
            return _invalid_format(f"{cls.__name__} format", text)

        return Ok(FullArtifactSectionId(f"{full_artifact_id}{cls.delimiter}{local_id}"))
