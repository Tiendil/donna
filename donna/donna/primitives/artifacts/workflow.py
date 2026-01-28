from typing import TYPE_CHECKING, ClassVar, Iterable, cast

from donna.core.errors import ErrorsList
from donna.core.result import Err, Ok, Result
from donna.domain.ids import ArtifactSectionId, FullArtifactId
from donna.machine.artifacts import Artifact, ArtifactSection, ArtifactSectionConfig, ArtifactSectionMeta
from donna.machine.errors import ArtifactValidationError
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
    ways_to_fix: list[str] = ["Ensure that the artifact contains the section with the specified start operation ID."]
    start_operation_id: ArtifactSectionId


class SectionIsNotAnOperation(ArtifactValidationError):
    code: str = "donna.workflows.section_is_not_an_operation"
    message: str = "Section `{error.workflow_section_id}` is not an operation and cannot be part of the workflow."
    ways_to_fix: list[str] = ["Ensure that the section has a kind of one of operation primitives."]
    workflow_section_id: ArtifactSectionId


class FinalOperationHasTransitions(ArtifactValidationError):
    code: str = "donna.workflows.final_operation_has_transitions"
    message: str = "Final operation `{error.workflow_section_id}` should not have outgoing transitions."
    ways_to_fix: list[str] = [
        "Approach A: Remove all outgoing transitions from this operation.",
        "Approach B: Change the `fsm_mode` of this operation from `final` to `normal`",
        "Approach C: Remove the `fsm_mode` setting from this operation, as `normal` is the default.",
    ]
    workflow_section_id: ArtifactSectionId


class NoOutgoingTransitions(ArtifactValidationError):
    code: str = "donna.workflows.no_outgoing_transitions"
    message: str = (
        "Operation `{error.workflow_section_id}` must have at least one outgoing transition or be marked as final."
    )
    ways_to_fix: list[str] = [
        "Approach A: Add at least one outgoing transition from this operation.",
        "Approach B: Change the kind of this operation to `donna.lib.finish`",
        "Approach C: Mark this operation as final by setting its `fsm_mode` to `final`.",
    ]
    workflow_section_id: ArtifactSectionId


def find_workflow_sections(start_operation_id: ArtifactSectionId, artifact: Artifact) -> set[ArtifactSectionId]:
    workflow_sections = set()
    to_visit = [start_operation_id]

    while to_visit:
        current = to_visit.pop()

        if current in workflow_sections:
            continue

        workflow_sections.add(current)

        section_result = artifact.get_section(current)
        if section_result.is_err():
            continue

        section = section_result.unwrap()

        if not isinstance(section.meta, OperationMeta):
            continue

        to_visit.extend(section.meta.allowed_transtions)

    return workflow_sections


class WorkflowConfig(ArtifactSectionConfig):
    start_operation_id: ArtifactSectionId


class WorkflowMeta(ArtifactSectionMeta):
    start_operation_id: ArtifactSectionId

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
        self, artifact: Artifact, section_id: ArtifactSectionId
    ) -> Result[None, ErrorsList]:
        section_result = artifact.get_section(section_id)
        if section_result.is_err():
            return Err(section_result.unwrap_err())

        section = section_result.unwrap()

        if not isinstance(section.meta, WorkflowMeta):
            raise NotImplementedError("Workflow section is not workflow")

        start_operation_id = section.meta.start_operation_id

        errors: ErrorsList = []

        start_operation_result = artifact.get_section(start_operation_id)
        if start_operation_result.is_err():
            errors.extend(start_operation_result.unwrap_err())
            errors.append(
                WrongStartOperation(
                    artifact_id=artifact.id, section_id=section_id, start_operation_id=start_operation_id
                )
            )

        workflow_sections = find_workflow_sections(start_operation_id, artifact)

        for workflow_section_id in workflow_sections:
            workflow_section_result = artifact.get_section(workflow_section_id)
            if workflow_section_result.is_err():
                errors.extend(workflow_section_result.unwrap_err())
                continue
            workflow_section = workflow_section_result.unwrap()

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

        if errors:
            return Err(errors)

        return Ok(None)
