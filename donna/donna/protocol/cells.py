import base64
import uuid

import pydantic

from donna.core.entities import BaseEntity

MetaValue = str | int | bool | None


class Cell(BaseEntity):
    id: uuid.UUID = pydantic.Field(default_factory=uuid.uuid4)
    content: str | None
    meta: dict[str, MetaValue] = pydantic.Field(default_factory=dict)

    # TODO: we may want to make queue items frozen later
    model_config = pydantic.ConfigDict(frozen=False)

    @classmethod
    def build(cls, kind: str, media_type: str | None, content: str | None, **meta: MetaValue) -> "Cell":
        cell = cls(content=content)
        cell.set_meta("kind", kind)

        if media_type is not None:
            cell.set_meta("media_type", media_type)

        for key, value in meta.items():
            cell.set_meta(key, value)

        return cell

    @classmethod
    def build_meta(cls, kind: str, **meta: MetaValue) -> "Cell":
        return cls.build(kind=kind, media_type=None, content="", **meta)

    @classmethod
    def build_markdown(cls, kind: str, content: str, **meta: MetaValue) -> "Cell":
        return cls.build(kind=kind, media_type="text/markdown", content=content, **meta)

    # TODO: refactor to base62 (without `_` and `-` characters)
    def short_id(self) -> str:
        return base64.urlsafe_b64encode(self.id.bytes).rstrip(b"=").decode()

    def set_meta(self, key: str, value: str | int | bool | None) -> None:
        if key in self.meta:
            raise NotImplementedError(f"Meta key '{key}' is already set")

        self.meta[key] = value


def cell_donna_message(content: str) -> Cell:
    return Cell.build_markdown(kind="donna_message", content=content)
