"""Python artifact that exposes directive kind definitions."""

from donna.domain.ids import ArtifactLocalId, FullArtifactLocalId
from donna.machine.artifacts import Section
from donna.machine.templates import DirectiveConfig
from donna.primitives.directives import GoTo, View

PYTHON_MODULE_SECTION_KIND_ID = FullArtifactLocalId.parse("donna.operations.python_module")

view_directive_entity = View()
goto_directive_entity = GoTo()

artifact_title = "Directive Kinds"
artifact_description = "Definitions for directive kinds exposed as Python module sections."
artifact_kind = FullArtifactLocalId.parse("donna.artifacts.python")

view_directive = Section(
    title="View",
    description=(
        "Instructs the agent how to view a specification.\n\n"
        "Example:\n\n"
        "{{ donna.directives.view('<specification_id>') }}"
    ),
    config=DirectiveConfig(
        id=ArtifactLocalId("view"),
        kind=PYTHON_MODULE_SECTION_KIND_ID,
        analyze_id="donna.directives.view",
    ),
    entity=view_directive_entity,
)

goto_directive = Section(
    title="Go To",
    description=(
        "Instructs the agent to proceed to the specified operation in the workflow.\n\n"
        "Example:\n\n"
        "{{ donna.directives.goto('<operation_id>') }}"
    ),
    config=DirectiveConfig(
        id=ArtifactLocalId("goto"),
        kind=PYTHON_MODULE_SECTION_KIND_ID,
        analyze_id="goto",
    ),
    entity=goto_directive_entity,
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
