"""Python artifact that exposes directive kind definitions."""

from donna.domain.ids import ArtifactLocalId, FullArtifactLocalId
from donna.machine.artifacts import ArtifactConfig, ArtifactConstructor, SectionConstructor
from donna.machine.templates import DirectiveConfig
from donna.primitives.directives import GoTo, View

PYTHON_MODULE_SECTION_KIND_ID = FullArtifactLocalId.parse("donna.operations.python_module")

view_directive_entity = View()
goto_directive_entity = GoTo()

artifact = ArtifactConstructor(
    title="Directive Kinds",
    description="Definitions for directive kinds exposed as Python module sections.",
    config=ArtifactConfig(kind=FullArtifactLocalId.parse("donna.artifacts.python")),
)

view_directive = SectionConstructor(
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

goto_directive = SectionConstructor(
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
    "artifact",
    "goto_directive",
    "view_directive",
]
