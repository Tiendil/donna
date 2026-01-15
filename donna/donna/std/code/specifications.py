from typing import Any

import jinja2
from jinja2.runtime import Context

from donna.domain.ids import ArtifactKindId, FullArtifactId, NamespaceId, RendererKindId
from donna.machine.artifacts import Artifact, ArtifactKind, ArtifactMeta, ArtifactSection, ArtifactSectionMeta
from donna.machine.cells import Cell
from donna.machine.templates import RendererKind
from donna.world.markdown import ArtifactSource
from donna.world.templates import RenderMode


class SpecificationKind(ArtifactKind):
    def construct_artifact(self, source: ArtifactSource) -> "Artifact":
        description = None

        description = source.head.merged_configs().get("description", description)
        description = description or ""

        title = source.head.title or str(source.id)

        sections = []

        # TODO: do we need to process that via section kinds?
        #       most likely yes — this is a way to unify artifacts processing
        for raw_section in source.tail:
            section = ArtifactSection(
                id=None,
                kind=None,
                title=raw_section.title or "",
                description=raw_section.as_original_markdown(with_title=False),
                meta=ArtifactSectionMeta())
            sections.append(section)

        # TODO: Should we add somewhere `content=source.as_original_markdown()`
        spec = Artifact(
            id=source.id,
            kind=self.id,
            title=title,
            description=description,
            meta=ArtifactMeta(),
            sections=sections
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
