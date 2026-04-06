from typing import Any, Sequence

from pydantic_core import core_schema

from donna.core.errors import ErrorsList
from donna.core.result import Err, Ok, Result
from donna.domain import errors as domain_errors
from donna.domain.id_paths import IdPath, IdPathPattern, _invalid_format, _pydantic_type_error, _pydantic_value_error


def _is_artifact_slug_part(part: str) -> bool:
    if not part:
        return False

    allowed_characters = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-")

    if any(character not in allowed_characters for character in part):
        return False

    return any(character not in ".-" for character in part)


class ArtifactId(IdPath):
    __slots__ = ()
    delimiter = ":"
    validate_json = True

    @classmethod
    def _validate_parts(cls, parts: Sequence[str]) -> bool:
        return all(_is_artifact_slug_part(part) for part in parts)

    def to_full_local(self, local_id: "ArtifactSectionId") -> "FullArtifactSectionId":
        return FullArtifactSectionId(f"{self}:{local_id}")

    @classmethod
    def parse(cls, text: str) -> Result["ArtifactId", ErrorsList]:
        if not isinstance(text, str) or not text:
            return _invalid_format(cls.__name__, text)

        if not cls.delimiter:
            return _invalid_format(cls.__name__, text)

        if not cls.validate(text):
            return _invalid_format(cls.__name__, text)

        return Ok(cls(text))


class ArtifactIdPattern(IdPathPattern["ArtifactId"]):
    __slots__ = ()
    id_class = ArtifactId

    @classmethod
    def _validate_pattern_part(cls, part: str) -> bool:
        if part in {"*", "**"}:
            return True

        return _is_artifact_slug_part(part)


class _ColonPath(IdPath):
    __slots__ = ()
    delimiter = ":"


class ArtifactSectionId(str):
    __slots__ = ()

    def __new__(cls, value: str) -> "ArtifactSectionId":
        if not cls.validate(value):
            raise domain_errors.InvalidIdentifier(value=value)

        return super().__new__(cls, value)

    @classmethod
    def validate(cls, value: str) -> bool:
        if not isinstance(value, str):
            return False
        return value.isidentifier()

    @classmethod
    def parse(cls, text: str) -> Result["ArtifactSectionId", ErrorsList]:
        if not isinstance(text, str) or not text:
            return _invalid_format(cls.__name__, text)

        if not cls.validate(text):
            return _invalid_format(cls.__name__, text)

        return Ok(cls(text))

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: Any) -> core_schema.CoreSchema:  # noqa: CCR001

        def validate(v: Any) -> "ArtifactSectionId":
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


class FullArtifactSectionId(_ColonPath):
    __slots__ = ()
    min_parts = 2
    validate_json = True

    @classmethod
    def _validate_parts(cls, parts: Sequence[str]) -> bool:
        if len(parts) < cls.min_parts:
            return False

        return ArtifactId.validate(cls.delimiter.join(parts[:-1])) and ArtifactSectionId.validate(parts[-1])

    def __str__(self) -> str:
        return f"{self.artifact_id}{self.delimiter}{self.local_id}"

    @property
    def artifact_id(self) -> ArtifactId:
        return ArtifactId(self.delimiter.join(self.parts[:-1]))

    @property
    def full_artifact_id(self) -> ArtifactId:
        return self.artifact_id

    @property
    def local_id(self) -> ArtifactSectionId:
        return ArtifactSectionId(self.parts[-1])

    @property
    def short(self) -> str:
        parts = str(self).split(self.delimiter)
        new_parts = [part[0] for part in parts[:-2]] + parts[-2:]
        return self.delimiter.join(new_parts)

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

        full_artifact_id_result = ArtifactId.parse(artifact_part)
        errors = full_artifact_id_result.err()
        if errors is not None:
            return Err(errors)

        artifact_id = full_artifact_id_result.ok()
        if artifact_id is None:
            return _invalid_format(f"{cls.__name__} format", text)

        local_id_result = ArtifactSectionId.parse(local_part)
        local_errors = local_id_result.err()
        if local_errors is not None:
            return Err(local_errors)

        local_id = local_id_result.ok()
        if local_id is None:
            return _invalid_format(f"{cls.__name__} format", text)

        return Ok(cls(f"{artifact_id}{cls.delimiter}{local_id}"))
