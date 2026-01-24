from typing import TYPE_CHECKING, ClassVar, Iterable, cast

from donna.domain.ids import ArtifactLocalId, FullArtifactId, FullArtifactLocalId
from donna.machine.artifacts import (
    Artifact,
    ArtifactSection,
    ArtifactSectionConfig,
    ArtifactSectionKind,
    ArtifactSectionMeta,
)
from donna.machine.cells import Cell
from donna.machine.operations import FsmMode, OperationMeta
from donna.world import markdown

if TYPE_CHECKING:
    from donna.machine.changes import Change
    from donna.machine.tasks import Task, WorkUnit


def find_not_reachable_operations(
    start_id: FullArtifactLocalId,  # noqa: CCR001
    transitions: dict[FullArtifactLocalId, set[FullArtifactLocalId]],
) -> set[FullArtifactLocalId]:
    reachable = set()
    to_visit = [start_id]

    while to_visit:
        current = to_visit.pop()

        if current in reachable:
            continue

        reachable.add(current)

        to_visit.extend(transitions.get(current, ()))

    all_operations = set()

    for from_id, target_ids in transitions.items():
        all_operations.add(from_id)
        all_operations.update(target_ids)

    return all_operations - reachable


class WorkflowConfig(ArtifactSectionConfig):
    start_operation_id: ArtifactLocalId


class WorkflowMeta(ArtifactSectionMeta):
    start_operation_id: FullArtifactLocalId

    def cells_meta(self) -> dict[str, object]:
        return {"start_operation_id": str(self.start_operation_id)}


class WorkflowKind(ArtifactSectionKind):
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
        return WorkflowMeta(start_operation_id=artifact_id.to_full_local(workflow_config.start_operation_id))

    def execute_section(self, task: "Task", unit: "WorkUnit", section: ArtifactSection) -> Iterable["Change"]:
        from donna.machine.changes import ChangeAddWorkUnit

        if not isinstance(section.meta, WorkflowMeta):
            raise NotImplementedError("Workflow section is missing workflow metadata.")

        yield ChangeAddWorkUnit(task_id=task.id, operation_id=section.meta.start_operation_id)

    def validate_section(  # noqa: CCR001, CFQ001
        self, artifact: Artifact, section_id: ArtifactLocalId
    ) -> tuple[bool, list[Cell]]:
        section = artifact.get_section(section_id)

        if section is None:
            raise NotImplementedError("Trying to validate an section that does not exist in the artifact.")

        if not isinstance(section.meta, WorkflowMeta):
            return False, [
                Cell.build_meta(
                    kind="artifact_kind_validation",
                    id=str(artifact.id),
                    status="failure",
                    message=f"Section '{section_id}' does not have workflow metadata.",
                )
            ]

        start_operation_id = section.meta.start_operation_id

        if artifact.get_section(start_operation_id.local_id) is None:
            return False, [
                Cell.build_meta(
                    kind="artifact_kind_validation",
                    id=str(artifact.id),
                    status="failure",
                    message=f"Start operation ID '{start_operation_id}' does not exist in the workflow.",
                )
            ]

        transitions = {}

        for section in artifact.sections:
            if not isinstance(section.meta, OperationMeta):
                return False, [
                    Cell.build_meta(
                        kind="artifact_kind_validation",
                        id=str(artifact.id),
                        status="failure",
                        message=f"Section '{section.id}' is not an operation and cannot be part of the workflow.",
                    )
                ]

            section_full_id = artifact.id.to_full_local(section.id) if section.id is not None else None

            if section.meta.fsm_mode == FsmMode.final and section.meta.allowed_transtions:
                return False, [
                    Cell.build_meta(
                        kind="artifact_kind_validation",
                        id=str(artifact.id),
                        status="failure",
                        message=f"Final operation '{section_full_id}' should not have outgoing transitions.",
                    )
                ]

            if section.meta.fsm_mode == FsmMode.start and section_full_id != start_operation_id:
                return False, [
                    Cell.build_meta(
                        kind="artifact_kind_validation",
                        id=str(artifact.id),
                        status="failure",
                        message=(
                            f"Operation '{section_full_id}' is marked as start but does not match the workflow's start"
                            f" operation ID '{start_operation_id}'."
                        ),
                    )
                ]

            if section.meta.fsm_mode == FsmMode.normal and not section.meta.allowed_transtions:
                return False, [
                    Cell.build_meta(
                        kind="artifact_kind_validation",
                        id=str(artifact.id),
                        status="failure",
                        message=(
                            f"Operation '{section_full_id}' must have at least one allowed transition or be marked as"
                            " final."
                        ),
                    )
                ]

            assert section_full_id is not None
            transitions[section_full_id] = set(section.meta.allowed_transtions)

        not_reachable_operations = find_not_reachable_operations(
            start_id=start_operation_id,
            transitions=transitions,
        )

        if not_reachable_operations:
            return False, [
                Cell.build_meta(
                    kind="artifact_kind_validation",
                    id=str(artifact.id),
                    status="failure",
                    message="The following operations are not reachable from the start operation: "
                    f"{', '.join(str(op_id) for op_id in not_reachable_operations)}.",
                )
            ]

        return True, [
            Cell.build_meta(
                kind="artifact_kind_validation",
                id=str(artifact.id),
                status="success",
            )
        ]
