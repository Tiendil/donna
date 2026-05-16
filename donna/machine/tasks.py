import copy
from typing import TYPE_CHECKING, Any

from donna.core.entities import BaseEntity
from donna.core.errors import ErrorsList
from donna.core.result import Ok, Result, unwrap_to_error
from donna.domain.artifact_ids import ArtifactSectionId, split_artifact_section_id
from donna.domain.internal_ids import TaskId, WorkUnitId

if TYPE_CHECKING:
    from donna.machine.changes import Change


class Task(BaseEntity):
    id: TaskId
    workflow_id: ArtifactSectionId
    context: dict[str, Any]

    @classmethod
    def build(cls, id: TaskId, workflow_id: ArtifactSectionId) -> "Task":
        return Task(
            id=id,
            workflow_id=workflow_id,
            context={},
        )


class WorkUnit(BaseEntity):
    id: WorkUnitId
    task_id: TaskId
    operation_id: ArtifactSectionId
    context: dict[str, Any]

    @classmethod
    def build(
        cls,
        id: WorkUnitId,
        task_id: TaskId,
        operation_id: ArtifactSectionId,
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
        from donna.context.context import context
        from donna.machine import journal as machine_journal
        from donna.workspaces.artifacts import ArtifactRenderContext
        from donna.workspaces.templates import RenderMode

        render_context = ArtifactRenderContext(
            primary_mode=RenderMode.execute,
            current_task=task,
            current_work_unit=self,
        )
        ctx = context()
        with ctx.current_operation_id.scope(self.operation_id):
            operation_parts = split_artifact_section_id(self.operation_id)
            assert operation_parts is not None
            artifact = ctx.artifacts.load(operation_parts.artifact_id, render_context).unwrap()
            operation = artifact.get_section(operation_parts.section_id).unwrap()
            operation_kind = ctx.primitives.resolve(operation.kind).unwrap()

            machine_journal.add(
                actor_id="donna",
                message=operation.title,
            ).unwrap()

            changes = operation_kind.execute_section(task, self, artifact, operation.id).unwrap()

        return Ok(changes)
