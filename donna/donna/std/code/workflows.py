from donna.domain.ids import NamespaceId, OperationId
from donna.machine.artifacts import Artifact, ArtifactInfo, ArtifactKind
from donna.machine.cells import Cell
from donna.world.markdown import ArtifactSource, SectionSource
from donna.machine import operations
from donna.world.primitives_register import register


class Workflow(Artifact):
    start_operation_id: OperationId
    operations: list[operations.Operation]

    def get_operation(self, operation_id: OperationId) -> operations.Operation | None:
        for operation in self.operations:
            if operation.info.id == operation_id:
                return operation
        return None

    def cells(self) -> list["Cell"]:
        return [Cell.build_markdown(kind=self.info.kind, content=self.info.description, id=str(self.info.id))]


def construct_operation(section: SectionSource) -> list[operations.Operation]:

    data = section.merged_configs()

    operation_kind = register().operations.get(data["kind"])

    operation = operation_kind.construct(section)

    return operation


class WorkflowKind(ArtifactKind):
    def construct(self, source: ArtifactSource) -> "Artifact":
        description = None

        description = source.head.merged_configs().get("description", description)

        title = source.head.title or str(source.id)

        operation_list = [construct_operation(section) for section in source.tail]

        spec = Workflow(
            info=ArtifactInfo(kind=self.id, id=source.id, title=title, description=description),
            start_operation_id=source.head.merged_configs()["start_operation_id"],
            operations=operation_list,
        )

        return spec


workflow_kind = WorkflowKind(
    id="workflow",
    namespace_id=NamespaceId("workflows"),
    description="A workflow that defines a statem machine for the agent to follow.",
)
