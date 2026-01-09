from donna.domain.ids import NamespaceId
from donna.machine.artifacts import Artifact, ArtifactInfo, ArtifactKind
from donna.machine.cells import Cell
from donna.world.markdown import ArtifactSource
from donna.machine import workflows
from donna.machine import operations


class Workflow(Artifact):
    workflow: workflows.Workflow
    operations: list[operations.Operation]

    def cells(self) -> list["Cell"]:
        return [Cell.build_markdown(kind="specification", content=self.content, id=str(self.info.id))]


class WorkflowKind(ArtifactKind):
    def construct(self, source: ArtifactSource) -> "Artifact":
        description = None

        for config in source.head.configs:
            data = config.structured_data()
            description = data.get("description", description)

        title = source.head.title or str(source.id)
        description = description or ""

        workflow = None
        operation_list = []

        spec = Workflow(
            info=ArtifactInfo(kind=self.id, id=source.id, title=title, description=description),
            workflow=workflow,
            operations=operation_list,
        )

        return spec


workflow_kind = WorkflowKind(
    id="workflow",
    namespace_id=NamespaceId("workflows"),
    description="A workflow that defines a statem machine for the agent to follow.",
)
