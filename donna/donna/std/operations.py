"""Python artifact that exposes section kind definitions."""

from donna.domain.ids import ArtifactLocalId, FullArtifactLocalId
from donna.machine.artifacts import ArtifactSection, ArtifactSectionKindMeta
from donna.primitives.artifacts import ArtifactSectionTextKind, PythonModuleSectionKind
from donna.primitives.operations import FinishWorkflowKind, RequestActionKind

PYTHON_MODULE_SECTION_KIND_ID = FullArtifactLocalId.parse("donna.operations.python_module")

text_section_kind_entity = ArtifactSectionTextKind()
python_module_section_kind_entity = PythonModuleSectionKind()
request_action_kind_entity = RequestActionKind()
finish_workflow_kind_entity = FinishWorkflowKind()

artifact_title = "Operation Section Kinds"
artifact_description = "Definitions for operation-related section kinds exposed as Python module sections."
artifact_kind = FullArtifactLocalId.parse("donna.artifacts.python")

text_section_kind = ArtifactSection(
    title="Text Section",
    description="",
    id=ArtifactLocalId("text"),
    kind=PYTHON_MODULE_SECTION_KIND_ID,
    meta=ArtifactSectionKindMeta(section_kind=text_section_kind_entity),
)

python_module_section_kind = ArtifactSection(
    title="Python module attribute",
    description="",
    id=ArtifactLocalId("python_module"),
    kind=PYTHON_MODULE_SECTION_KIND_ID,
    meta=ArtifactSectionKindMeta(section_kind=python_module_section_kind_entity),
)

request_action_kind = ArtifactSection(
    title="Request Action",
    description="",
    id=ArtifactLocalId("request_action"),
    kind=PYTHON_MODULE_SECTION_KIND_ID,
    meta=ArtifactSectionKindMeta(section_kind=request_action_kind_entity),
)

finish_workflow_kind = ArtifactSection(
    title="Finish Workflow",
    description="",
    id=ArtifactLocalId("finish_workflow"),
    kind=PYTHON_MODULE_SECTION_KIND_ID,
    meta=ArtifactSectionKindMeta(section_kind=finish_workflow_kind_entity),
)

__all__ = [
    "artifact_description",
    "artifact_kind",
    "artifact_title",
    "finish_workflow_kind",
    "python_module_section_kind",
    "request_action_kind",
    "text_section_kind",
]
