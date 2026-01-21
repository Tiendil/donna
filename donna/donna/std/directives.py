"""Python artifact that exposes directive kind definitions."""

from typing import Any

import jinja2
from jinja2.runtime import Context

from donna.domain.ids import ArtifactLocalId, FullArtifactId, FullArtifactLocalId
from donna.machine.artifacts import SectionConstructor
from donna.machine.templates import DirectiveKind, DirectiveSectionMeta
from donna.world.templates import RenderMode


class View(DirectiveKind):

    @jinja2.pass_context
    def __call__(self, context: Context, *argv: Any, **kwargs: Any) -> Any:
        render_mode: RenderMode = context["render_mode"]
        directive_id = kwargs.get("directive_id")

        if argv is None or len(argv) != 1:
            raise ValueError("View directive requires exactly one argument: specificatin_id")

        artifact_id = FullArtifactId.parse(str(argv[0]))

        match render_mode:
            case RenderMode.cli:
                return self.render_cli(context, artifact_id)

            case RenderMode.analysis:
                return self.render_analyze(context, artifact_id, directive_id)

            case _:
                raise NotImplementedError(f"Render mode {render_mode} not implemented in View directive.")

    def render_cli(self, context: Context, specification_id: FullArtifactId) -> str:
        return f"donna artifacts view '{specification_id}'"

    def render_analyze(
        self,
        context: Context,
        specification_id: FullArtifactId,
        directive_id: FullArtifactLocalId | None,
    ) -> str:
        if directive_id is None:
            raise ValueError("Directive id is required to render analysis for View directive.")

        return f"$$donna {directive_id} {specification_id} donna$$"


class GoTo(DirectiveKind):

    @jinja2.pass_context
    def __call__(self, context: Context, *argv: Any, **kwargs: Any) -> Any:
        render_mode: RenderMode = context["render_mode"]

        if argv is None or len(argv) != 1:
            raise ValueError("GoTo directive requires exactly one argument: next_operation_id")

        artifact_id = context["artifact_id"]

        next_operation_id = artifact_id.to_full_local(argv[0])

        match render_mode:
            case RenderMode.cli:
                return self.render_cli(context, next_operation_id)

            case RenderMode.analysis:
                return self.render_analyze(context, next_operation_id)

            case _:
                raise NotImplementedError(f"Render mode {render_mode} not implemented in GoTo directive.")

    def render_cli(self, context: Context, next_operation_id: FullArtifactLocalId) -> str:
        return f"donna sessions action-request-completed <action-request-id> '{next_operation_id}'"

    def render_analyze(self, context: Context, next_operation_id: FullArtifactLocalId) -> str:
        return f"$$donna goto {next_operation_id} donna$$"


PYTHON_MODULE_SECTION_KIND_ID = FullArtifactLocalId.parse("donna.operations:python_module")

view_directive_entity = View()
goto_directive_entity = GoTo()

view_directive = SectionConstructor(
    id=ArtifactLocalId("view"),
    kind=PYTHON_MODULE_SECTION_KIND_ID,
    title="View",
    description="Instructs the agent how to view a specification.",
    meta=DirectiveSectionMeta(
        name="Specification reference",
        example="{{ donna.directives.view('<specification_id>') }}",
    ),
    entity=view_directive_entity,
)

goto_directive = SectionConstructor(
    id=ArtifactLocalId("goto"),
    kind=PYTHON_MODULE_SECTION_KIND_ID,
    title="Go To",
    description="Instructs the agent to proceed to the specified operation in the workflow.",
    meta=DirectiveSectionMeta(
        name="Go To Operation",
        example="{{ donna.directives.goto('<operation_id>') }}",
    ),
    entity=goto_directive_entity,
)


__all__ = [
    "GoTo",
    "View",
    "goto_directive",
    "view_directive",
]
