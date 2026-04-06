from typing import Any

from pydantic_core import core_schema

from donna.core.errors import ErrorsList
from donna.core.result import Ok, Result
from donna.domain import errors as domain_errors
from donna.domain.id_paths import _invalid_format, _pydantic_type_error, _pydantic_value_error


def _is_artifact_slug_part(part: str) -> bool:
    if not part:
        return False

    allowed_characters = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-")

    if any(character not in allowed_characters for character in part):
        return False

    return any(character not in ".-" for character in part)


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
    def parse(cls, text: str) -> Result["Identifier", ErrorsList]:
        if not isinstance(text, str) or not text:
            return _invalid_format(cls.__name__, text)

        if not cls.validate(text):
            return _invalid_format(cls.__name__, text)

        return Ok(cls(text))

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


class SectionId(Identifier):
    __slots__ = ()
