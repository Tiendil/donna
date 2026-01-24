"""Python artifact that exposes section kind definitions."""

from donna.domain.ids import ArtifactLocalId, FullArtifactLocalId
from donna.machine.artifacts import ArtifactSection, ArtifactSectionKindMeta, ArtifactSectionMeta
from donna.primitives.artifacts.python import PythonModuleSectionKind
from donna.primitives.artifacts.specification import ArtifactSectionTextKind
from donna.primitives.operations.finish_workflow import FinishWorkflowKind
from donna.primitives.operations.request_action import RequestActionKind
from donna.world.sources.markdown import Config as MarkdownSourceConfig

PYTHON_MODULE_SECTION_KIND_ID = FullArtifactLocalId.parse("donna.operations.python_module")
PYTHON_ARTIFACT_KIND_ID = FullArtifactLocalId.parse("donna.artifacts.python")
PRIMARY_SECTION_ID = MarkdownSourceConfig().default_primary_section_id

text_section_kind_entity = ArtifactSectionTextKind()
python_module_section_kind_entity = PythonModuleSectionKind()
request_action_kind_entity = RequestActionKind()
finish_workflow_kind_entity = FinishWorkflowKind()

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
