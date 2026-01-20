"""Python artifact that exposes artifact kind definitions."""

from donna.domain.ids import ArtifactId, ArtifactLocalId, FullArtifactLocalId, NamespaceId, WorldId
from donna.machine.artifacts import PythonArtifact
from donna.std.code.specifications import SpecificationKind
from donna.std.code.workflows import WorkflowKind

ARTIFACTS_WORLD_ID = WorldId("donna")
ARTIFACTS_NAMESPACE_ID = NamespaceId("python")
ARTIFACTS_ARTIFACT_ID = ArtifactId("artifacts")


def artifact_kind_id(local_id: str) -> FullArtifactLocalId:
    return FullArtifactLocalId(
        (ARTIFACTS_WORLD_ID, ARTIFACTS_NAMESPACE_ID, ARTIFACTS_ARTIFACT_ID, ArtifactLocalId(local_id))
    )


specification_kind = SpecificationKind(
    id=artifact_kind_id("specification"),
    title="Specification",
    namespace_id=NamespaceId("specifications"),
    description="A specification that define various aspects of the current project.",
)


workflow_kind = WorkflowKind(
    id=artifact_kind_id("workflow"),
    title="Workflow",
    namespace_id=NamespaceId("workflows"),
    description="A workflow that defines a state machine for the agent to follow.",
)


python_artifact_kind = PythonArtifact(
    id=artifact_kind_id("python"),
    title="Python Artifact",
    namespace_id=NamespaceId("python"),
    description="A Python module artifact.",
)

__all__ = [
    "artifact_kind_id",
    "python_artifact_kind",
    "specification_kind",
    "workflow_kind",
]
