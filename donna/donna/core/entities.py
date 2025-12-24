import tomllib
from typing import Any, TypeVar

import pydantic
import tomli_w

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

    def to_toml(self) -> str:
        data = self.model_dump(mode="json")
        return tomli_w.dumps(data)

    @classmethod
    def from_toml(cls: type[BASE_ENTITY], toml_str: str) -> BASE_ENTITY:
        data = tomllib.loads(toml_str)
        return cls.model_validate(data)
