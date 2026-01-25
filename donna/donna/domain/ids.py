from typing import Any

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


class ArtifactId(str):
    __slots__ = ()

    def __new__(cls, value: str) -> "ArtifactId":
        if not cls.validate(value):
            raise NotImplementedError(f"Invalid ArtifactId: '{value}'")

        return super().__new__(cls, value)

    @classmethod
    def validate(cls, value: str) -> bool:
        if not isinstance(value, str) or not value:
            return False

        parts = value.split(":")
        return all(part.isidentifier() for part in parts)

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: Any) -> core_schema.CoreSchema:

        def validate(v: Any) -> "ArtifactId":
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


class PythonImportPath(str):
    __slots__ = ()

    def __new__(cls, value: str) -> "PythonImportPath":
        if not cls.validate(value):
            raise NotImplementedError(f"Invalid PythonImportPath: '{value}'")

        return super().__new__(cls, value)

    @classmethod
    def validate(cls, value: str) -> bool:
        if not isinstance(value, str) or not value:
            return False

        parts = value.split(".")
        return all(part.isidentifier() for part in parts)

    @classmethod
    def parse(cls, text: str) -> "PythonImportPath":
        return cls(text)

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: Any) -> core_schema.CoreSchema:

        def validate(v: Any) -> "PythonImportPath":
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


class FullArtifactId(tuple[WorldId, ArtifactId]):
    __slots__ = ()

    def __str__(self) -> str:
        return f"{self.world_id}:{self.artifact_id}"

    @property
    def world_id(self) -> WorldId:
        return self[0]

    @property
    def artifact_id(self) -> ArtifactId:
        return self[1]

    def to_full_local(self, local_id: "ArtifactLocalId") -> "FullArtifactLocalId":
        return FullArtifactLocalId((self.world_id, self.artifact_id, local_id))

    @classmethod
    def parse(cls, text: str) -> "FullArtifactId":
        parts = text.split(":", maxsplit=1)

        if len(parts) != 2:
            raise NotImplementedError(f"Invalid FullArtifactId format: '{text}'")

        world_id = WorldId(parts[0])
        artifact_id = ArtifactId(parts[1])

        return FullArtifactId((world_id, artifact_id))

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: Any) -> core_schema.CoreSchema:

        def validate(v: Any) -> "FullArtifactId":
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


class ArtifactLocalId(Identifier):
    __slots__ = ()


class OperationId(ArtifactLocalId):
    __slots__ = ()


class FullArtifactLocalId(tuple[WorldId, ArtifactId, ArtifactLocalId]):
    __slots__ = ()

    def __str__(self) -> str:
        return f"{self.world_id}:{self.artifact_id}:{self.local_id}"

    @property
    def world_id(self) -> WorldId:
        return self[0]

    @property
    def artifact_id(self) -> ArtifactId:
        return self[1]

    @property
    def full_artifact_id(self) -> FullArtifactId:
        return FullArtifactId((self.world_id, self.artifact_id))

    @property
    def local_id(self) -> ArtifactLocalId:
        return self[2]

    @classmethod
    def parse(cls, text: str) -> "FullArtifactLocalId":
        try:
            artifact_part, local_part = text.rsplit(":", maxsplit=1)
        except ValueError as exc:
            raise NotImplementedError(f"Invalid FullArtifactLocalId format: '{text}'") from exc

        full_artifact_id = FullArtifactId.parse(artifact_part)

        return FullArtifactLocalId(
            (full_artifact_id.world_id, full_artifact_id.artifact_id, ArtifactLocalId(local_part))
        )

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: Any) -> core_schema.CoreSchema:

        def validate(v: Any) -> "FullArtifactLocalId":
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
