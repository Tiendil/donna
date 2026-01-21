"""Python artifact that exposes artifact kind definitions."""

from donna.domain.ids import ArtifactLocalId, FullArtifactLocalId
from donna.machine.artifacts import (
    ArtifactConfig,
    ArtifactConstructor,
    ArtifactSectionConfig,
    PythonArtifact,
    SectionConstructor,
)
from donna.std.code.specifications import SpecificationKind
from donna.std.code.workflows import WorkflowKind

PYTHON_MODULE_SECTION_KIND_ID = FullArtifactLocalId.parse("donna.operations:python_module")

specification_kind_entity = SpecificationKind()
workflow_kind_entity = WorkflowKind()
python_artifact_kind = PythonArtifact()

artifact = ArtifactConstructor(
    title="Artifact Kinds",
    description="Definitions for artifact kinds exposed as Python module sections.",
    config=ArtifactConfig(kind=FullArtifactLocalId.parse("donna.artifacts:python")),
)

specification_kind = SectionConstructor(
    title="Specification",
    description="A specification that define various aspects of the current project.",
    config=ArtifactSectionConfig(
        id=ArtifactLocalId("specification"),
        kind=PYTHON_MODULE_SECTION_KIND_ID,
    ),
    entity=specification_kind_entity,
)

workflow_kind = SectionConstructor(
    title="Workflow",
    description="A workflow that defines a state machine for the agent to follow.",
    config=ArtifactSectionConfig(
        id=ArtifactLocalId("workflow"),
        kind=PYTHON_MODULE_SECTION_KIND_ID,
    ),
    entity=workflow_kind_entity,
)

python_artifact_kind_section = SectionConstructor(
    title="Python Artifact",
    description="A Python module artifact.",
    config=ArtifactSectionConfig(
        id=ArtifactLocalId("python"),
        kind=PYTHON_MODULE_SECTION_KIND_ID,
    ),
    entity=python_artifact_kind,
)

__all__ = [
    "python_artifact_kind",
    "python_artifact_kind_section",
    "specification_kind",
    "workflow_kind",
    "artifact",
]
