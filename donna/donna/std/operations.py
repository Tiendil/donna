"""Python artifact that exposes section kind definitions."""

import donna.lib as lib
from donna.domain.ids import ArtifactLocalId, FullArtifactLocalId
from donna.machine.artifacts import ArtifactSection, ArtifactSectionKindMeta, ArtifactSectionMeta

PYTHON_MODULE_SECTION_KIND_ID = FullArtifactLocalId.parse("donna.operations.python_module")
PYTHON_ARTIFACT_KIND_ID = FullArtifactLocalId.parse("donna.artifacts.python")
PRIMARY_SECTION_ID = ArtifactLocalId("primary")

primary_section = ArtifactSection(
    title="Operation Section Kinds",
    description="Definitions for operation-related section kinds exposed as Python module sections.",
    id=PRIMARY_SECTION_ID,
    kind=PYTHON_ARTIFACT_KIND_ID,
    primary=True,
    meta=ArtifactSectionMeta(),
)

text_section_kind = ArtifactSection(
    title="Text Section",
    description="",
    id=ArtifactLocalId("text"),
    kind=PYTHON_MODULE_SECTION_KIND_ID,
    meta=ArtifactSectionKindMeta(section_kind=lib.text),
)

python_module_section_kind = ArtifactSection(
    title="Python module attribute",
    description="",
    id=ArtifactLocalId("python_module"),
    kind=PYTHON_MODULE_SECTION_KIND_ID,
    meta=ArtifactSectionKindMeta(section_kind=lib.python_module_section),
)

request_action_kind = ArtifactSection(
    title="Request Action",
    description="",
    id=ArtifactLocalId("request_action"),
    kind=PYTHON_MODULE_SECTION_KIND_ID,
    meta=ArtifactSectionKindMeta(section_kind=lib.request_action),
)

finish_workflow_kind = ArtifactSection(
    title="Finish Workflow",
    description="",
    id=ArtifactLocalId("finish_workflow"),
    kind=PYTHON_MODULE_SECTION_KIND_ID,
    meta=ArtifactSectionKindMeta(section_kind=lib.finish),
)
