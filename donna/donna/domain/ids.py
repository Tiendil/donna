from typing import Any, Sequence

from pydantic_core import core_schema


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


class InternalId(str):
    __slots__ = ()

    def __new__(cls, value: str) -> "InternalId":
        if not cls.validate(value):
            raise NotImplementedError(f"Invalid InternalId: '{value}'")

        return super().__new__(cls, value)

    @classmethod
    def build(cls, prefix: str, value: int) -> "InternalId":
        return cls(f"{prefix}-{value}-{_id_crc(value)}")

    @classmethod
    def validate(cls, id: str) -> bool:
        _prefix, value, crc = id.rsplit("-", maxsplit=2)
        expected_crc = _id_crc(int(value))
        return crc == expected_crc

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: Any) -> core_schema.CoreSchema:

        def validate(v: Any) -> "InternalId":
            if isinstance(v, cls):
                return v

            if not isinstance(v, str):
                raise TypeError(f"{cls.__name__} must be a str, got {type(v).__name__}")

            if not cls.validate(v):
                raise ValueError(f"Invalid {cls.__name__}: {v!r}")

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
        if not value.isidentifier():
            raise NotImplementedError(f"Invalid identifier: '{value}'")

        return super().__new__(cls, value)

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: Any) -> core_schema.CoreSchema:

        def validate(v: Any) -> "Identifier":
            if isinstance(v, cls):
                return v

            if not isinstance(v, str):
                raise TypeError(f"{cls.__name__} must be a str, got {type(v).__name__}")

            if not v.isidentifier():
                raise ValueError(f"Invalid {cls.__name__}: {v!r}")

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
            raise NotImplementedError(f"Invalid {cls.__name__}: '{text}'")

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
                raise TypeError(f"{cls.__name__} must be a str, got {type(v).__name__}")

            if not cls.validate(v):
                raise ValueError(f"Invalid {cls.__name__}: {v!r}")

            return cls(v)

        return cls._build_pydantic_schema(validate)


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
    def parse(cls, text: str) -> "PythonImportPath":
        return cls(text)


class FullArtifactId(ColonPath):
    __slots__ = ()
    min_parts = 2
    validate_json = True

    def __str__(self) -> str:
        return f"{self.world_id}:{self.artifact_id}"

    @property
    def world_id(self) -> WorldId:
        return WorldId(self.parts[0])

    @property
    def artifact_id(self) -> ArtifactId:
        return ArtifactId(self.delimiter.join(self.parts[1:]))

    def to_full_local(self, local_id: "ArtifactSectionId") -> "FullArtifactSectionId":
        return FullArtifactSectionId(f"{self}:{local_id}")

    @classmethod
    def parse(cls, text: str) -> "FullArtifactId":
        parts = text.split(":", maxsplit=1)

        if len(parts) != 2:
            raise NotImplementedError(f"Invalid FullArtifactId format: '{text}'")

        world_id = WorldId(parts[0])
        artifact_id = ArtifactId(parts[1])

        return FullArtifactId(f"{world_id}:{artifact_id}")


class FullArtifactIdPattern(tuple[str, ...]):
    __slots__ = ()

    def __str__(self) -> str:
        return ":".join(self)

    @classmethod
    def parse(cls, text: str) -> "FullArtifactIdPattern":  # noqa: CCR001
        if not isinstance(text, str) or not text:
            raise NotImplementedError(f"Invalid FullArtifactIdPattern: '{text}'")

        parts = text.split(":")

        if any(part == "" for part in parts):
            raise NotImplementedError(f"Invalid FullArtifactIdPattern: '{text}'")

        for part in parts:
            if part in {"*", "**"}:
                continue

            if not part.isidentifier():
                raise NotImplementedError(f"Invalid FullArtifactIdPattern: '{text}'")

        return cls(parts)

    def matches_full_id(self, full_id: "FullArtifactId") -> bool:
        return _match_pattern_parts(self, str(full_id).split(":"))

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: Any) -> core_schema.CoreSchema:

        def validate(v: Any) -> "FullArtifactIdPattern":
            if isinstance(v, cls):
                return v

            if not isinstance(v, str):
                raise TypeError(f"{cls.__name__} must be a str, got {type(v).__name__}")

            return cls.parse(v)

        str_then_validate = core_schema.no_info_after_validator_function(
            validate,
            core_schema.str_schema(),
        )

        return core_schema.json_or_python_schema(
            json_schema=str_then_validate,
            python_schema=core_schema.no_info_plain_validator_function(validate),
            serialization=core_schema.to_string_ser_schema(),
        )


class ArtifactSectionId(Identifier):
    __slots__ = ()

    @classmethod
    def parse(cls, text: str) -> "ArtifactSectionId":
        return cls(text)


class FullArtifactSectionId(ColonPath):
    __slots__ = ()
    min_parts = 3
    validate_json = True

    def __str__(self) -> str:
        return f"{self.world_id}:{self.artifact_id}:{self.local_id}"

    @property
    def world_id(self) -> WorldId:
        return WorldId(self.parts[0])

    @property
    def artifact_id(self) -> ArtifactId:
        return ArtifactId(self.delimiter.join(self.parts[1:-1]))

    @property
    def full_artifact_id(self) -> FullArtifactId:
        return FullArtifactId(f"{self.world_id}:{self.artifact_id}")

    @property
    def local_id(self) -> ArtifactSectionId:
        return ArtifactSectionId(self.parts[-1])

    @classmethod
    def parse(cls, text: str) -> "FullArtifactSectionId":
        try:
            artifact_part, local_part = text.rsplit(":", maxsplit=1)
        except ValueError as exc:
            raise NotImplementedError(f"Invalid FullArtifactSectionId format: '{text}'") from exc

        full_artifact_id = FullArtifactId.parse(artifact_part)

        return FullArtifactSectionId(f"{full_artifact_id}:{ArtifactSectionId(local_part)}")
