
from typing import Any, TypeVar

import pydantic

BASE_ENTITY = TypeVar("BASE_ENTITY", bound="BaseEntity")


class BaseEntity(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(
        str_strip_whitespace=True,
        validate_default=True,
        extra="forbid",
        frozen=True,
        validate_assignment=True,
        from_attributes=False,
    )

    def replace(self: BASE_ENTITY, **kwargs: Any) -> BASE_ENTITY:
        return self.model_copy(update=kwargs, deep=True)

    def to_json(self) -> str:
        # TODO: make indent configurable
        return self.model_dump_json(indent=2)

    @classmethod
    def from_json(cls: type[BASE_ENTITY], json_data: str) -> BASE_ENTITY:
        return cls.model_validate_json(json_data)
