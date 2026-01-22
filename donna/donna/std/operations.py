"""Python artifact that exposes section kind definitions."""

from donna.domain.ids import ArtifactLocalId, FullArtifactLocalId
from donna.machine.artifacts import ArtifactConfig, ArtifactConstructor, ArtifactSectionConfig, SectionConstructor
from donna.primitives.artifacts import ArtifactSectionTextKind, PythonModuleSectionKind
from donna.primitives.operations import FinishWorkflowKind, RequestActionKind

PYTHON_MODULE_SECTION_KIND_ID = FullArtifactLocalId.parse("donna.operations.python_module")

text_section_kind_entity = ArtifactSectionTextKind()
python_module_section_kind_entity = PythonModuleSectionKind()
request_action_kind_entity = RequestActionKind()
finish_workflow_kind_entity = FinishWorkflowKind()

artifact = ArtifactConstructor(
    title="Operation Section Kinds",
    description="Definitions for operation-related section kinds exposed as Python module sections.",
    config=ArtifactConfig(kind=FullArtifactLocalId.parse("donna.artifacts.python")),
)

text_section_kind = SectionConstructor(
    title="Text Section",
    description="",
    config=ArtifactSectionConfig(
        id=ArtifactLocalId("text"),
        kind=PYTHON_MODULE_SECTION_KIND_ID,
    ),
    entity=text_section_kind_entity,
)

python_module_section_kind = SectionConstructor(
    title="Python module attribute",
    description="",
    config=ArtifactSectionConfig(
        id=ArtifactLocalId("python_module"),
        kind=PYTHON_MODULE_SECTION_KIND_ID,
    ),
    entity=python_module_section_kind_entity,
)

request_action_kind = SectionConstructor(
    title="Request Action",
    description="",
    config=ArtifactSectionConfig(
        id=ArtifactLocalId("request_action"),
        kind=PYTHON_MODULE_SECTION_KIND_ID,
    ),
    entity=request_action_kind_entity,
)

finish_workflow_kind = SectionConstructor(
    title="Finish Workflow",
    description="",
    config=ArtifactSectionConfig(
        id=ArtifactLocalId("finish_workflow"),
        kind=PYTHON_MODULE_SECTION_KIND_ID,
    ),
    entity=finish_workflow_kind_entity,
)

__all__ = [
    "artifact",
    "finish_workflow_kind",
    "python_module_section_kind",
    "request_action_kind",
    "text_section_kind",
]
