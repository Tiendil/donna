import copy
from typing import TYPE_CHECKING, Any

from donna.core.entities import BaseEntity
from donna.core.errors import ErrorsList
from donna.core.result import Ok, Result, unwrap_to_error
from donna.domain.ids import FullArtifactSectionId, TaskId, WorkUnitId
from donna.protocol.cells import Cell
from donna.protocol.utils import instant_output

if TYPE_CHECKING:
    from donna.machine.changes import Change


class Task(BaseEntity):
    id: TaskId
    context: dict[str, Any]

    @classmethod
    def build(cls, id: TaskId) -> "Task":
        return Task(
            id=id,
            context={},
        )


class WorkUnit(BaseEntity):
    id: WorkUnitId
    task_id: TaskId
    operation_id: FullArtifactSectionId
    context: dict[str, Any]

    @classmethod
    def build(
        cls,
        id: WorkUnitId,
        task_id: TaskId,
        operation_id: FullArtifactSectionId,
        context: dict[str, Any] | None = None,
    ) -> "WorkUnit":

        if context is None:
            context = {}

        unit = cls(
            task_id=task_id,
            id=id,
            operation_id=operation_id,
            context=copy.deepcopy(context),
        )

        return unit

    @unwrap_to_error
    def run(self, task: Task) -> Result[list["Change"], ErrorsList]:
        from donna.machine import artifacts as machine_artifacts
        from donna.machine.primitives import resolve_primitive
        from donna.workspaces.artifacts import ArtifactRenderContext
        from donna.workspaces.templates import RenderMode

        render_context = ArtifactRenderContext(
            primary_mode=RenderMode.execute,
            current_task=task,
            current_work_unit=self,
        )
        operation = machine_artifacts.resolve(self.operation_id, render_context).unwrap()
        operation_kind = resolve_primitive(operation.kind).unwrap()

        log_message = f"{self.operation_id}: {operation.title}"
        log_cell = Cell.build(kind="donna_log", media_type="text/plain", content=log_message)
        instant_output([log_cell])

        changes = list(operation_kind.execute_section(task, self, operation))

        return Ok(changes)
