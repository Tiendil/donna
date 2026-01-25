"""Python artifact that exposes artifact section kind definitions."""

from donna.domain.ids import ArtifactLocalId, FullArtifactLocalId
from donna.lib import python_artifact_kind, specification_kind_entity, workflow_kind_entity
from donna.machine.artifacts import ArtifactSection, ArtifactSectionKindMeta, ArtifactSectionMeta

PYTHON_MODULE_SECTION_KIND_ID = FullArtifactLocalId.parse("donna.operations.python_module")
PYTHON_ARTIFACT_KIND_ID = FullArtifactLocalId.parse("donna.artifacts.python")
PRIMARY_SECTION_ID = ArtifactLocalId("primary")

primary_section = ArtifactSection(
    title="Artifact Section Kinds",
    description="Definitions for artifact section kinds exposed as Python module sections.",
    id=PRIMARY_SECTION_ID,
    kind=PYTHON_ARTIFACT_KIND_ID,
    primary=True,
    meta=ArtifactSectionMeta(),
)

specification_kind = ArtifactSection(
    title="Specification",
    description="A specification that define various aspects of the current project.",
    id=ArtifactLocalId("specification"),
    kind=PYTHON_MODULE_SECTION_KIND_ID,
    meta=ArtifactSectionKindMeta(section_kind=specification_kind_entity),
)

workflow_kind = ArtifactSection(
    title="Workflow",
    description="A workflow that defines a state machine for the agent to follow.",
    id=ArtifactLocalId("workflow"),
    kind=PYTHON_MODULE_SECTION_KIND_ID,
    meta=ArtifactSectionKindMeta(section_kind=workflow_kind_entity),
)

python_artifact_kind_section = ArtifactSection(
    title="Python Artifact",
    description="A Python module artifact.",
    id=ArtifactLocalId("python"),
    kind=PYTHON_MODULE_SECTION_KIND_ID,
    meta=ArtifactSectionKindMeta(section_kind=python_artifact_kind),
)
