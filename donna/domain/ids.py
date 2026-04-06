from typing import Any

from pydantic_core import core_schema

from donna.domain import errors as domain_errors
from donna.domain.artifact_ids import _is_artifact_slug_part
from donna.domain.id_paths import _pydantic_type_error, _pydantic_value_error


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
