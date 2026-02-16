import copy
from typing import TYPE_CHECKING, Any

from donna.core.entities import BaseEntity
from donna.core.errors import ErrorsList
from donna.core.result import Ok, Result, unwrap_to_error
from donna.domain.ids import FullArtifactSectionId, TaskId, WorkUnitId
from donna.protocol.utils import instant_output

if TYPE_CHECKING:
    from donna.machine.changes import Change


class Task(BaseEntity):
    id: TaskId
    workflow_id: FullArtifactSectionId
    context: dict[str, Any]

    @classmethod
    def build(cls, id: TaskId, workflow_id: FullArtifactSectionId) -> "Task":
        return Task(
            id=id,
            workflow_id=workflow_id,
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
        from donna.machine import journal as machine_journal
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

        journal_record = machine_journal.add(
            actor_id="donna",
            message=operation.title,
            current_task_id=str(task.id),
            current_work_unit_id=str(self.id),
            current_operation_id=str(self.operation_id),
        ).unwrap()

        instant_output(journal_record)

        changes = operation_kind.execute_section(task, self, operation).unwrap()

        return Ok(changes)
