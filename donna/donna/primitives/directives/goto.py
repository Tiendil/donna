from typing import Any

import jinja2
from jinja2.runtime import Context

from donna.domain.ids import FullArtifactLocalId
from donna.machine.templates import DirectiveKind, DirectiveSectionMeta
from donna.world.templates import RenderMode


class GoTo(DirectiveKind):
    @jinja2.pass_context
    def __call__(self, context: Context, *argv: Any, **kwargs: Any) -> Any:
        render_mode: RenderMode = context["render_mode"]
        meta = kwargs.get("meta")

        if argv is None or len(argv) != 1:
            raise ValueError("GoTo directive requires exactly one argument: next_operation_id")

        artifact_id = context["artifact_id"]

        next_operation_id = artifact_id.to_full_local(argv[0])

        match render_mode:
            case RenderMode.cli:
                return self.render_cli(context, next_operation_id)

            case RenderMode.analysis:
                return self.render_analyze(context, next_operation_id, meta)

            case _:
                raise NotImplementedError(f"Render mode {render_mode} not implemented in GoTo directive.")

    def render_cli(self, context: Context, next_operation_id: FullArtifactLocalId) -> str:
        return f"donna sessions action-request-completed <action-request-id> '{next_operation_id}'"

    def render_analyze(
        self,
        context: Context,
        next_operation_id: FullArtifactLocalId,
        meta: DirectiveSectionMeta | None,
    ) -> str:
        if meta is None:
            raise ValueError("Directive meta is required to render analysis for GoTo directive.")

        return f"$$donna {meta.analyze_id} {next_operation_id} donna$$"
