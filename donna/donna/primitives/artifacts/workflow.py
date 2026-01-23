from donna.domain.ids import FullArtifactLocalId
from donna.machine.artifacts import Artifact, ArtifactConfig, ArtifactContent, ArtifactKind, ArtifactSection
from donna.machine.cells import Cell
from donna.machine.operations import FsmMode, OperationMeta
from donna.machine.workflows import WorkflowMeta


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


class WorkflowKind(ArtifactKind):
    def construct_artifact(self, source: ArtifactContent, sections: list[ArtifactSection]) -> Artifact:  # noqa: CCR001
        title = source.head.title or str(source.id)
        description = source.head.description
        kind_id = ArtifactConfig.parse_obj(source.head.config).kind

        start_operation_id: FullArtifactLocalId | None = None

        for section in sections:
            assert isinstance(section.meta, OperationMeta)
            if section.meta.fsm_mode == FsmMode.start:
                if section.id is None:
                    raise NotImplementedError(f"Workflow '{source.id}' has a start operation without an id.")
                start_operation_id = source.id.to_full_local(section.id)
                break
        else:
            raise NotImplementedError(f"Workflow '{source.id}' does not have a start operation.")

        assert start_operation_id is not None

        return Artifact(
            id=source.id,
            kind=kind_id,
            title=title,
            description=description,
            meta=WorkflowMeta(start_operation_id=start_operation_id),
            sections=sections,
        )

    def validate_artifact(self, artifact: Artifact) -> tuple[bool, list[Cell]]:  # noqa: CCR001
        assert isinstance(artifact.meta, WorkflowMeta)

        start_operation_id: FullArtifactLocalId = artifact.meta.start_operation_id

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
            assert isinstance(section.meta, OperationMeta)
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
