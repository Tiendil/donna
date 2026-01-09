from donna.domain.ids import NamespaceId, OperationId
from donna.machine.artifacts import Artifact, ArtifactInfo, ArtifactKind
from donna.machine.cells import Cell
from donna.world.markdown import ArtifactSource, SectionSource
from donna.machine import workflows
from donna.machine import operations


class Workflow(Artifact):
    operation_id: OperationId
    operations: list[operations.Operation]

    def cells(self) -> list["Cell"]:
        return [Cell.build_markdown(kind="specification", content=self.content, id=str(self.info.id))]


def construct_operation(section: SectionSource) -> list[operations.Operation]:
    data = section.structured_data()

    return operations.Operation(
        id=data["id"],
        kind=data["kind"],
        title=section.title or "Untitled Operation",
        results=data["results"],
    )


class WorkflowKind(ArtifactKind):
    def construct(self, source: ArtifactSource) -> "Artifact":
        description = None

        for config in source.head.configs:
            data = config.structured_data()
            description = data.get("description", description)

        title = source.head.title or str(source.id)
        description = description or ""

        operation_list = [construct_operation(section) for section in source.tail]

        spec = Workflow(
            info=ArtifactInfo(kind=self.id, id=source.id, title=title, description=description),
            operation_id=source.head.merged_configs()["operation_id"],
            operations=operation_list,
        )

        return spec


workflow_kind = WorkflowKind(
    id="workflow",
    namespace_id=NamespaceId("workflows"),
    description="A workflow that defines a statem machine for the agent to follow.",
)
