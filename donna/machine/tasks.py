import copy
from collections.abc import Mapping
from typing import TYPE_CHECKING

from donna.core.entities import BaseEntity
from donna.core.errors import ErrorsList
from donna.core.result import Ok, Result, unwrap_to_error
from donna.domain.artifact_ids import ArtifactSectionId, split_artifact_section_id
from donna.domain.internal_ids import TaskId, WorkUnitId
from donna.machine.context import context

if TYPE_CHECKING:
    from donna.machine.changes import Change


class Task(BaseEntity):
    id: TaskId
    workflow_id: ArtifactSectionId
    context: dict[str, object]

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
    context: dict[str, object]

    @classmethod
    def build(
        cls,
        id: WorkUnitId,
        task_id: TaskId,
        operation_id: ArtifactSectionId,
        context: Mapping[str, object] | None = None,
    ) -> "WorkUnit":

        if context is None:
            context = {}

        unit = cls(
            task_id=task_id,
            id=id,
            operation_id=operation_id,
            context=copy.deepcopy(dict(context)),
        )

        return unit

    @unwrap_to_error
    def run(self, task: Task) -> Result[list["Change"], ErrorsList]:
        ctx = context()
        with ctx.current_operation_id.scope(self.operation_id):
            operation_parts = split_artifact_section_id(self.operation_id)
            assert operation_parts is not None
            artifact = ctx.artifacts.load_for_execution(operation_parts.artifact_id, task, self).unwrap()
            operation = artifact.get_section(operation_parts.section_id).unwrap()
            operation_kind = ctx.primitives.resolve(operation.kind).unwrap()

            ctx.journal.add(
                actor_id="donna",
                message=operation.title,
            ).unwrap()

            changes = operation_kind.execute_section(task, self, artifact, operation.id).unwrap()

        return Ok(changes)
