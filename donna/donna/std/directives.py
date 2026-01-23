"""Python artifact that exposes directive kind definitions."""

from donna.domain.ids import ArtifactLocalId, FullArtifactLocalId
from donna.machine.artifacts import ArtifactSection
from donna.machine.templates import DirectiveSectionMeta
from donna.primitives.directives import GoTo, View

PYTHON_MODULE_SECTION_KIND_ID = FullArtifactLocalId.parse("donna.operations.python_module")

view_directive_entity = View()
goto_directive_entity = GoTo()

artifact_title = "Directive Kinds"
artifact_description = "Definitions for directive kinds exposed as Python module sections."
artifact_kind = FullArtifactLocalId.parse("donna.artifacts.python")

view_directive = ArtifactSection(
    title="View",
    description=(
        "Instructs the agent how to view a specification.\n\n"
        "Example:\n\n"
        "{{ donna.directives.view('<specification_id>') }}"
    ),
    id=ArtifactLocalId("view"),
    kind=PYTHON_MODULE_SECTION_KIND_ID,
    meta=DirectiveSectionMeta(
        analyze_id="donna.directives.view",
        directive=view_directive_entity,
    ),
)

goto_directive = ArtifactSection(
    title="Go To",
    description=(
        "Instructs the agent to proceed to the specified operation in the workflow.\n\n"
        "Example:\n\n"
        "{{ donna.directives.goto('<operation_id>') }}"
    ),
    id=ArtifactLocalId("goto"),
    kind=PYTHON_MODULE_SECTION_KIND_ID,
    meta=DirectiveSectionMeta(
        analyze_id="goto",
        directive=goto_directive_entity,
    ),
)


__all__ = [
    "GoTo",
    "View",
    "artifact_description",
    "artifact_kind",
    "artifact_title",
    "goto_directive",
    "view_directive",
]
