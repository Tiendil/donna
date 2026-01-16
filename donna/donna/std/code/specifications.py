from typing import Any

import jinja2
from jinja2.runtime import Context

from donna.domain.ids import ArtifactKindId, FullArtifactId, NamespaceId, RendererKindId
from donna.machine.artifacts import Artifact, ArtifactKind, ArtifactMeta
from donna.machine.templates import RendererKind
from donna.world.markdown import ArtifactSource
from donna.world.templates import RenderMode


class SpecificationKind(ArtifactKind):
    def construct_artifact(self, source: ArtifactSource) -> "Artifact":
        title = source.head.title or str(source.id)
        description = source.head.as_original_markdown(with_title=False)

        sections = [self.construct_section(source.id, section) for section in source.tail]

        spec = Artifact(
            id=source.id, kind=self.id, title=title, description=description, meta=ArtifactMeta(), sections=sections
        )

        return spec


specification_kind = SpecificationKind(
    id=ArtifactKindId("specification"),
    namespace_id=NamespaceId("specifications"),
    description="A specification that define various aspects of the current project.",
)


class View(RendererKind):

    @jinja2.pass_context
    def __call__(self, context: Context, *argv: Any, **kwargs: Any) -> Any:
        render_mode: RenderMode = context["render_mode"]

        if argv is None or len(argv) != 1:
            raise ValueError("View renderer requires exactly one argument: specificatin_id")

        artifact_id = FullArtifactId.parse(str(argv[0]))

        match render_mode:
            case RenderMode.cli:
                return self.render_cli(context, artifact_id)

            case RenderMode.analysis:
                return self.render_analyze(context, artifact_id)

            case _:
                raise NotImplementedError(f"Render mode {render_mode} not implemented in View renderer.")

    def render_cli(self, context: Context, specification_id: FullArtifactId) -> str:
        return f"donna artifacts view '{specification_id}'"

    def render_analyze(self, context: Context, specification_id: FullArtifactId) -> str:
        return f"$$donna {self.id} {specification_id} donna$$"


view_renderer = View(
    id=RendererKindId("view"),
    name="Specification reference",
    description="Instructs the agent how to view a specification.",
    example="{{ view('<specification_id>') }}",
)
