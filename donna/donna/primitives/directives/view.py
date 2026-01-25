from typing import Any

import jinja2
from jinja2.runtime import Context

from donna.domain.ids import FullArtifactId
from donna.machine.templates import DirectiveKind
from donna.world.templates import RenderMode


class View(DirectiveKind):
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
        return f"$$donna {self.analyze_id} {specification_id} donna$$"
