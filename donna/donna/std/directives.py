"""Python artifact that exposes directive kind definitions."""

from typing import Any

import jinja2
from jinja2.runtime import Context

from donna.domain.ids import ArtifactId, ArtifactLocalId, FullArtifactId, FullArtifactLocalId, WorldId
from donna.machine.templates import DirectiveKindSection
from donna.world.templates import RenderMode

DIRECTIVES_WORLD_ID = WorldId("donna")
DIRECTIVES_ARTIFACT_ID = ArtifactId("directives")


def directive_kind_id(local_id: str) -> FullArtifactLocalId:
    return FullArtifactLocalId((DIRECTIVES_WORLD_ID, DIRECTIVES_ARTIFACT_ID, ArtifactLocalId(local_id)))


class View(DirectiveKindSection):

    @jinja2.pass_context
    def __call__(self, context: Context, *argv: Any, **kwargs: Any) -> Any:
        render_mode: RenderMode = context["render_mode"]

        if argv is None or len(argv) != 1:
            raise ValueError("View directive requires exactly one argument: specificatin_id")

        artifact_id = FullArtifactId.parse(str(argv[0]))

        match render_mode:
            case RenderMode.cli:
                return self.render_cli(context, artifact_id)

            case RenderMode.analysis:
                return self.render_analyze(context, artifact_id)

            case _:
                raise NotImplementedError(f"Render mode {render_mode} not implemented in View directive.")

    def render_cli(self, context: Context, specification_id: FullArtifactId) -> str:
        return f"donna artifacts view '{specification_id}'"

    def render_analyze(self, context: Context, specification_id: FullArtifactId) -> str:
        return f"$$donna {self.id} {specification_id} donna$$"


class GoTo(DirectiveKindSection):

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


view_directive = View(
    id=directive_kind_id("view"),
    title="View",
    name="Specification reference",
    description="Instructs the agent how to view a specification.",
    example="{{ donna.directives.view('<specification_id>') }}",
)


goto_directive = GoTo(
    id=directive_kind_id("goto"),
    title="Go To",
    name="Go To Operation",
    description="Instructs the agent to proceed to the specified operation in the workflow.",
    example="{{ donna.directives.goto('<operation_id>') }}",
)


__all__ = [
    "GoTo",
    "View",
    "directive_kind_id",
    "goto_directive",
    "view_directive",
]
