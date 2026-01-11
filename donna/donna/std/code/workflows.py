from typing import Any

import jinja2
from jinja2.runtime import Context

from donna.domain.ids import (
    ArtifactKindId,
    FullArtifactId,
    FullArtifactLocalId,
    NamespaceId,
    OperationId,
    OperationKindId,
    RendererKindId,
)
from donna.machine.artifacts import Artifact, ArtifactInfo, ArtifactKind
from donna.machine.cells import Cell
from donna.machine.operations import Operation, OperationKind, OperationMode
from donna.machine.templates import RendererKind
from donna.world.markdown import ArtifactSource, SectionSource
from donna.world.primitives_register import register
from donna.world.templates import RenderMode


class Workflow(Artifact):
    start_operation_id: OperationId
    operations: list[Operation]

    @property
    def full_start_operation_id(self) -> FullArtifactLocalId:
        return self.info.id.to_full_local(self.start_operation_id)

    def get_operation(self, operation_id: OperationId) -> Operation | None:
        for operation in self.operations:
            if operation.id == operation_id:
                return operation
        return None

    def cells(self) -> list["Cell"]:
        return [Cell.build_markdown(kind=self.info.kind, content=self.info.description, id=str(self.info.id))]


def construct_operation(artifact_id: FullArtifactId, section: SectionSource) -> Operation:

    data = section.merged_configs()

    operation_kind = register().operations.get(OperationKindId(data["kind"]))
    assert isinstance(operation_kind, OperationKind)

    operation = operation_kind.construct(artifact_id, section)

    return operation


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
    def construct(self, source: ArtifactSource) -> "Artifact":  # type: ignore[override]
        description = None

        description = source.head.merged_configs().get("description", description)
        description = description or ""

        title = source.head.title or str(source.id)

        operation_list = [construct_operation(source.id, section) for section in source.tail]

        spec = Workflow(
            info=ArtifactInfo(kind=self.id, id=source.id, title=title, description=description),
            start_operation_id=source.head.merged_configs()["start_operation_id"],
            operations=operation_list,
        )

        return spec

    def validate_artifact(self, artifact: Artifact) -> list[Cell]:  # noqa: CCR001
        assert isinstance(artifact, Workflow)
        if artifact.get_operation(artifact.start_operation_id) is None:
            return [
                Cell.build_meta(
                    kind="artifact_kind_validation",
                    id=str(artifact.info.id),
                    status="failure",
                    message=f"Start operation ID '{artifact.start_operation_id}' does not exist in the workflow.",
                )
            ]

        transitions = {}

        for operation in artifact.operations:
            if operation.mode == OperationMode.final and operation.allowed_transtions:
                return [
                    Cell.build_meta(
                        kind="artifact_kind_validation",
                        id=str(artifact.info.id),
                        status="failure",
                        message=f"Final operation '{operation.id}' should not have outgoing transitions.",
                    )
                ]

            if operation.mode == OperationMode.normal and not operation.allowed_transtions:
                return [
                    Cell.build_meta(
                        kind="artifact_kind_validation",
                        id=str(artifact.info.id),
                        status="failure",
                        message=(
                            f"Operation '{operation.id}' must have at least one allowed transition or be marked as"
                            " final."
                        ),
                    )
                ]

            transitions[operation.full_id] = set(operation.allowed_transtions)

        not_reachable_operations = find_not_reachable_operations(
            start_id=artifact.full_start_operation_id,
            transitions=transitions,
        )

        if not_reachable_operations:
            return [
                Cell.build_meta(
                    kind="artifact_kind_validation",
                    id=str(artifact.info.id),
                    status="failure",
                    message=f"The following operations are not reachable from the start operation: "
                    f"{', '.join(str(op_id) for op_id in not_reachable_operations)}.",
                )
            ]

        return [
            Cell.build_meta(
                kind="artifact_kind_validation",
                id=str(artifact.info.id),
                status="success",
            )
        ]


workflow_kind = WorkflowKind(
    id=ArtifactKindId("workflow"),
    namespace_id=NamespaceId("workflows"),
    description="A workflow that defines a state machine for the agent to follow.",
)


class GoTo(RendererKind):

    @jinja2.pass_context
    def __call__(self, context: Context, *argv: Any, **kwargs: Any) -> Any:
        render_mode: RenderMode = context["render_mode"]

        artifact_id = context["artifact_id"]

        if argv is None or len(argv) != 1:
            raise ValueError("GoTo renderer requires exactly one argument: next_operation_id")

        next_operation_id = artifact_id.to_full_local(argv[0])

        match render_mode:
            case RenderMode.cli:
                return self.render_cli(context, next_operation_id)

            case RenderMode.analysis:
                return self.render_analyze(context, next_operation_id)

            case _:
                raise NotImplementedError(f"Render mode {render_mode} not implemented in GoTo renderer.")

    def render_cli(self, context: Context, next_operation_id: FullArtifactLocalId) -> str:
        return f"donna sessions action-request-completed <action-request-id> '{next_operation_id}'"

    def render_analyze(self, context: Context, next_operation_id: FullArtifactLocalId) -> str:
        return f"$$donna {self.id} {next_operation_id} donna$$"


goto_renderer = GoTo(
    id=RendererKindId("goto"),
    name="Go To Operation",
    description="Instructs the agent to proceed to the specified operation in the workflow.",
    example="{{ goto('<operation_id>') }}",
)
