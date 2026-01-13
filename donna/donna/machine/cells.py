import base64
import json
import uuid
from typing import Any

import pydantic
from pydantic_core import to_jsonable_python

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
    def build_text(cls, kind: str, content: str, **meta: MetaValue) -> "Cell":
        return cls.build(kind=kind, media_type="text/plain", content=content, **meta)

    @classmethod
    def build_markdown(cls, kind: str, content: str, **meta: MetaValue) -> "Cell":
        return cls.build(kind=kind, media_type="text/markdown", content=content, **meta)

    @classmethod
    def build_json(cls, kind: str, content: Any, **meta: MetaValue) -> "Cell":
        # TODO: we may want make indent configurable
        formated_content = json.dumps(to_jsonable_python(content), indent=2)
        return cls.build(kind=kind, media_type="application/json", content=formated_content, **meta)

    # TODO: refactor to base62 (without `_` and `-` characters)
    def short_id(self) -> str:
        return base64.urlsafe_b64encode(self.id.bytes).rstrip(b"=").decode()

    def set_meta(self, key: str, value: str | int | bool | None) -> None:
        if key in self.meta:
            raise NotImplementedError(f"Meta key '{key}' is already set")

        self.meta[key] = value

    def render(self) -> str:

        id = self.short_id()

        lines = [f"--DONNA-CELL {id} BEGIN--"]

        for meta_key, meta_value in self.meta.items():
            lines.append(f"{meta_key}: {meta_value}")

        if self.meta and self.content:
            lines.append("")

        if self.content:
            lines.append(self.content)

        lines.append(f"--DONNA-CELL {id} END--")

        cell = "\n".join(lines).strip()

        return cell


def cell_donna_message(content: str) -> Cell:
    return Cell.build_markdown(kind="donna_message", content=content)
