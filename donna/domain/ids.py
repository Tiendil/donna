from typing import Any

from pydantic_core import core_schema

from donna.domain import errors as domain_errors
from donna.domain.artifact_ids import _is_artifact_slug_part
from donna.domain.id_paths import _pydantic_type_error, _pydantic_value_error


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

    @property
    def short(self) -> str:
        return self.split("-")[1]

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

    @classmethod
    def validate(cls, value: str) -> bool:
        if not isinstance(value, str):
            return False

        return _is_artifact_slug_part(value)
