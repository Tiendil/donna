from typing import Any, Callable

from pydantic_core import core_schema

from donna.domain import types

_SESSION_COUNTERS: dict[Callable[[types.InternalId], types.InternalId], types.CounterId] = {
    types.WorkUnitId: types.CounterId("WU"),
    types.ActionRequestId: types.CounterId("AR"),
    types.TaskId: types.CounterId("T"),
    types.RecordId: types.CounterId("R"),
}


class RichInternalId:
    __slots__ = ("id", "value")

    id: types.CounterId
    value: int

    def __init__(self, id: types.CounterId, value: int) -> None:
        self.id = id
        self.value = value

    def to_int(self) -> int:
        return self.value

    def to_internal(self) -> types.InternalId:
        return types.InternalId(f"{self.id}-{self.value}-{self.crc()}")

    def crc(self) -> str:
        """Translates int into a compact string representation with a-zA-Z0-9 characters."""
        charset = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        base = len(charset)

        num = self.value
        if num == 0:
            return charset[0]

        chars = []
        while num > 0:
            num, rem = divmod(num, base)
            chars.append(charset[rem])

        chars.reverse()
        return "".join(chars)


class RichNestedId(tuple[str, ...]):
    __slots__ = ()

    def __new__(cls, value: str | tuple[str, ...]) -> "RichNestedId":
        if isinstance(value, str):
            parts = tuple(value.split(":"))
        else:
            parts = tuple(value)

        if not parts:
            raise ValueError("NestedId cannot be empty")

        return super().__new__(cls, parts)

    def to_nested(self) -> types.NestedId:
        return types.NestedId(":".join(self))


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


class NamespaceId(Identifier):
    __slots__ = ()


class ArtifactId(Identifier):
    __slots__ = ()


class FullArtifactId(tuple[WorldId, NamespaceId, ArtifactId]):
    __slots__ = ()

    def __str__(self) -> str:
        return f"{self.world_id}.{self.namespace_id}.{self.artifact_id}"

    @property
    def world_id(self) -> WorldId:
        return self[0]

    @property
    def namespace_id(self) -> NamespaceId:
        return self[1]

    @property
    def artifact_id(self) -> ArtifactId:
        return self[2]

    def to_full_local(self, local_id: "ArtifactLocalId") -> "FullArtifactLocalId":
        return FullArtifactLocalId((self.world_id, self.namespace_id, self.artifact_id, local_id))

    @classmethod
    def parse(cls, text: str) -> "FullArtifactId":
        parts = text.split(".", maxsplit=2)

        if len(parts) != 3:
            raise NotImplementedError(f"Invalid FullArtifactId format: '{text}'")

        world_id = WorldId(parts[0])
        namespace_id = NamespaceId(parts[1])
        artifact_id = ArtifactId(parts[2])

        return FullArtifactId((world_id, namespace_id, artifact_id))

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


class FullArtifactLocalId(tuple[WorldId, NamespaceId, ArtifactId, ArtifactLocalId]):
    __slots__ = ()

    def __str__(self) -> str:
        return f"{self.world_id}.{self.namespace_id}.{self.artifact_id}:{self.local_id}"

    @property
    def world_id(self) -> WorldId:
        return self[0]

    @property
    def namespace_id(self) -> NamespaceId:
        return self[1]

    @property
    def artifact_id(self) -> ArtifactId:
        return self[2]

    @property
    def full_artifact_id(self) -> FullArtifactId:
        return FullArtifactId((self.world_id, self.namespace_id, self.artifact_id))

    @property
    def local_id(self) -> ArtifactLocalId:
        return self[3]

    @classmethod
    def parse(cls, text: str) -> "FullArtifactLocalId":
        artifact_part, local_part = text.rsplit(":", maxsplit=1)
        parts = artifact_part.split(".", maxsplit=2)

        if len(parts) != 3:
            raise NotImplementedError(f"Invalid FullArtifactLocalId format: '{text}'")

        world_id = WorldId(parts[0])
        namespace_id = NamespaceId(parts[1])
        artifact_id = ArtifactId(parts[2])
        local_id = ArtifactLocalId(local_part)

        return FullArtifactLocalId((world_id, namespace_id, artifact_id, local_id))

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


def next_id[InternalIdType: types.InternalId](
    type_id: Callable[[types.InternalId], InternalIdType],
) -> InternalIdType:
    # TODO: the direction of this dependency is wrong (`domain` should not depend on `machine`).
    #       It is acceptable on the early stages of development, but should be fixed later.
    from donna.machine.counters import Counters

    counters = Counters.load()

    if type_id not in _SESSION_COUNTERS:
        raise NotImplementedError(f"No counter defined for type '{type_id}'")

    counter_id = _SESSION_COUNTERS[type_id]

    next_id = counters.next(counter_id)

    counters.save()

    id = RichInternalId(id=counter_id, value=next_id)

    return type_id(id.to_internal())


def create_internal_id_parser[InternalIdType: types.InternalId](
    type_id: Callable[[types.InternalId], InternalIdType],
) -> Callable[[str], InternalIdType]:
    def parser(text: str) -> InternalIdType:
        parts = text.split("-")

        if len(parts) != 3:
            raise ValueError(f"Invalid id format: '{text}'")

        counter_id, number, crc = parts

        if counter_id not in _SESSION_COUNTERS.values():
            raise NotImplementedError(f"Unknown counter id: '{counter_id}'")

        id = RichInternalId(id=types.CounterId(counter_id), value=int(number))

        if id.crc() != crc:
            raise NotImplementedError(f"Invalid crc for id: '{text}'")

        return type_id(id.to_internal())

    return parser


def create_nested_id_parser[InternalIdType: types.NestedId](
    type_id: Callable[[types.NestedId], InternalIdType],
) -> Callable[[str], InternalIdType]:
    def parser(text: str) -> InternalIdType:
        id = RichNestedId(text)
        return type_id(id.to_nested())

    return parser
