import base64
import uuid

import pydantic

from donna.core.entities import BaseEntity

MetaValue = str | int | bool | None


def to_meta_value(value: object) -> MetaValue:
    if isinstance(value, (str, int, bool)) or value is None:
        return value

    return str(value)


class Cell(BaseEntity):
    id: uuid.UUID = pydantic.Field(default_factory=uuid.uuid4)
    kind: str
    media_type: str | None
    content: str | None
    meta: dict[str, MetaValue] = pydantic.Field(default_factory=dict)

    @classmethod
    def build(cls, kind: str, media_type: str | None, content: str | None, **meta: MetaValue) -> "Cell":
        if media_type is None and content is not None:
            raise NotImplementedError("Cannot set content when media_type is None")

        return cls(kind=kind, media_type=media_type, content=content, meta=meta)

    @classmethod
    def build_meta(cls, kind: str, **meta: MetaValue) -> "Cell":
        return cls.build(kind=kind, media_type=None, content=None, **meta)

    @classmethod
    def build_markdown(cls, kind: str, content: str, **meta: MetaValue) -> "Cell":
        return cls.build(kind=kind, media_type="text/markdown", content=content, **meta)

    @property
    def short_id(self) -> str:
        return base64.urlsafe_b64encode(self.id.bytes).rstrip(b"=").decode()


def cell_donna_message(content: str) -> Cell:
    return Cell.build_markdown(kind="donna_message", content=content)
