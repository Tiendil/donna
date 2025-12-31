import uuid
import base64
import textwrap
import pydantic
from typing import Any

import xml.etree.ElementTree as ET

from donna.core.entities import BaseEntity
from donna.domain.types import ActionRequestId, StoryId, TaskId, WorkUnitId


class Cell(BaseEntity):
    id: uuid.UUID = pydantic.Field(default_factory=uuid.uuid4)
    content: str
    meta: dict[str, str | int | bool | None] = pydantic.Field(default_factory=dict)

    # TODO: we may want to make queue items frozen later
    model_config = pydantic.ConfigDict(frozen=False)

    @classmethod
    def build(cls, kind: str, media_type: str, content: str) -> "Cell":
        cell = cls(content=content)
        cell.set_meta("kind", kind)
        cell.set_meta("media_type", media_type)
        return cell

    @classmethod
    def build_text(cls, content: str) -> "Cell":
        return cls.build(kind="text", media_type="text/plain", content=content)

    @classmethod
    def build_markdown(cls, content: str) -> "Cell":
        return cls.build(kind="text", media_type="text/markdown", content=content)

    @classmethod
    def build_json(cls, content: Any) -> "Cell":
        # TODO: we may want make indent configurable
        formated_content = pydantic.json.dumps(content, indent=2)
        return cls.build(kind="data", media_type="application/json", content=formated_content)

    # TODO: refactor to base62 (without `_` and `-` characters)
    def short_id(self) -> str:
        return base64.urlsafe_b64encode(self.id.bytes).rstrip(b'=').decode()

    def set_meta(self, key: str, value: str | int | bool | None) -> None:
        if key in self.meta:
            raise NotImplementedError(f"Meta key '{key}' is already set")

        self.meta[key] = value

    def render(self) -> str:

        meta = "\n".join(f"{key}: {value}" for key, value in self.meta.items())

        cell = textwrap.dedent(
            """
        --DONNA-CELL-{id} BEGING--
        {meta}

        {content}
        --DONNA-CELL-{id} END--
        """
        ).format(content=self.content, meta=meta, id=self.short_id())

        return cell.strip()


class AgentCell(BaseEntity):
    story_id: StoryId | None
    task_id: TaskId | None
    work_unit_id: WorkUnitId | None

    def render(self) -> AgentCellHistory:

        cell = textwrap.dedent(
            """
        ##########################
        {meta}
        --------------------------
        {custom_body}
        """
        ).format(custom_body=self.custom_body(), meta=self.render_meta())

        return AgentCellHistory(work_unit_id=self.work_unit_id, body=cell.strip())

    def meta(self) -> dict[str, str]:
        return {
            "story_id": str(self.story_id),
            "task_id": str(self.task_id) if self.task_id is not None else "",
            "work_unit_id": (str(self.work_unit_id) if self.work_unit_id is not None else ""),
        }

    def render_meta(self) -> str:
        meta_lines = [f"{key}: {value}" for key, value in self.meta().items()]
        return "\n".join(meta_lines)

    def custom_body(self) -> str:
        raise NotImplementedError()


class AgentMessage(AgentCell):
    message: str
    action_request_id: ActionRequestId | None

    def meta(self) -> dict[str, str]:
        base_meta = super().meta()

        base_meta["action_request_id"] = str(self.action_request_id) if self.action_request_id is not None else ""

        return base_meta

    def custom_body(self) -> str:
        return self.message


class WorkflowCell(AgentCell):
    workflow_id: str
    name: str
    description: str

    def meta(self) -> dict[str, str]:
        base_meta = super().meta()
        base_meta["workflow_id"] = self.workflow_id
        return base_meta

    def custom_body(self) -> str:
        return f"# Workflow: {self.name}\n\n{self.description}"
