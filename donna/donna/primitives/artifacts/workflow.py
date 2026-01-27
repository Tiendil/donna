from typing import TYPE_CHECKING, ClassVar, Iterable, cast

from safe_result import Err, Ok, Result, ok

from donna.core.errors import ErrorsList
from donna.domain.ids import ArtifactLocalId, FullArtifactId
from donna.machine.artifacts import (
    Artifact,
    ArtifactSection,
    ArtifactSectionConfig,
    ArtifactSectionMeta,
    ArtifactValidationError,
)
from donna.machine.operations import FsmMode, OperationMeta
from donna.machine.primitives import Primitive
from donna.world import markdown
from donna.world.sources.markdown import MarkdownSectionMixin

if TYPE_CHECKING:
    from donna.machine.changes import Change
    from donna.machine.tasks import Task, WorkUnit


class WrongStartOperation(ArtifactValidationError):
    code: str = "donna.workflows.wrong_start_operation"
    message: str = "Can not find the start operation `{error.start_operation_id}` in the workflow."
    start_operation_id: ArtifactLocalId


class SectionIsNotAnOperation(ArtifactValidationError):
    code: str = "donna.workflows.section_is_not_an_operation"
    message: str = "Section `{error.workflow_section_id}` is not an operation and cannot be part of the workflow."
    workflow_section_id: ArtifactLocalId


class FinalOperationHasTransitions(ArtifactValidationError):
    code: str = "donna.workflows.final_operation_has_transitions"
    message: str = "Final operation `{error.workflow_section_id}` should not have outgoing transitions."
    workflow_section_id: ArtifactLocalId


class NoOutgoingTransitions(ArtifactValidationError):
    code: str = "donna.workflows.no_outgoing_transitions"
    message: str = (
        "Operation `{error.workflow_section_id}` must have at least one outgoing transition or be marked as final."
    )
    workflow_section_id: ArtifactLocalId


def find_not_reachable_operations(
    start_id: ArtifactLocalId,  # noqa: CCR001
    transitions: dict[ArtifactLocalId, set[ArtifactLocalId]],
) -> set[ArtifactLocalId]:
    reachable = set()
    to_visit = [start_id]

    while to_visit:
        current = to_visit.pop()

        if current in reachable:
            continue

        reachable.add(current)

        to_visit.extend(transitions.get(current, set()))

    all_operations = set()

    for from_id, target_ids in transitions.items():
        all_operations.add(from_id)
        all_operations.update(target_ids)

    return all_operations - reachable


class WorkflowConfig(ArtifactSectionConfig):
    start_operation_id: ArtifactLocalId


class WorkflowMeta(ArtifactSectionMeta):
    start_operation_id: ArtifactLocalId

    def cells_meta(self) -> dict[str, object]:
        return {"start_operation_id": str(self.start_operation_id)}


class Workflow(MarkdownSectionMixin, Primitive):
    config_class: ClassVar[type[WorkflowConfig]] = WorkflowConfig

    def markdown_construct_meta(
        self,
        artifact_id: FullArtifactId,
        source: markdown.SectionSource,
        section_config: ArtifactSectionConfig,
        description: str,
        primary: bool = False,
    ) -> ArtifactSectionMeta:
        workflow_config = cast(WorkflowConfig, section_config)
        return WorkflowMeta(start_operation_id=workflow_config.start_operation_id)

    def execute_section(self, task: "Task", unit: "WorkUnit", section: ArtifactSection) -> Iterable["Change"]:
        from donna.machine.changes import ChangeAddWorkUnit

        if not isinstance(section.meta, WorkflowMeta):
            raise NotImplementedError("Workflow section is missing workflow metadata.")

        full_id = section.artifact_id.to_full_local(section.meta.start_operation_id)

        yield ChangeAddWorkUnit(task_id=task.id, operation_id=full_id)

    def validate_section(  # noqa: CCR001, CFQ001
        self, artifact: Artifact, section_id: ArtifactLocalId
    ) -> Result[None, ErrorsList]:
        section = artifact.get_section(section_id)

        if section is None:
            raise NotImplementedError("Trying to validate a section that does not exist in the artifact.")

        if not isinstance(section.meta, WorkflowMeta):
            raise NotImplementedError("Workflow section is not workflow")

        start_operation_id = section.meta.start_operation_id

        errors: list[ArtifactValidationError] = []

        if artifact.get_section(start_operation_id) is None:
            errors.append(
                WrongStartOperation(
                    artifact_id=artifact.id, section_id=section_id, start_operation_id=start_operation_id
                )
            )

        transitions = {}

        for workflow_section in artifact.sections:
            if isinstance(workflow_section.meta, WorkflowMeta):
                continue

            if not isinstance(workflow_section.meta, OperationMeta):
                errors.append(
                    SectionIsNotAnOperation(
                        artifact_id=artifact.id, section_id=section.id, workflow_section_id=workflow_section.id
                    )
                )
                continue

            if workflow_section.meta.fsm_mode == FsmMode.final and workflow_section.meta.allowed_transtions:
                errors.append(
                    FinalOperationHasTransitions(
                        artifact_id=artifact.id, section_id=section_id, workflow_section_id=workflow_section.id
                    )
                )
                continue

            if workflow_section.meta.fsm_mode == FsmMode.final:
                continue

            if not workflow_section.meta.allowed_transtions:
                errors.append(
                    NoOutgoingTransitions(
                        artifact_id=artifact.id, section_id=section_id, workflow_section_id=workflow_section.id
                    )
                )

            transitions[workflow_section.id] = set(workflow_section.meta.allowed_transtions)

        if errors:
            return Err(errors)

        return Ok(None)
