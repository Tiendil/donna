import enum
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterator

import jinja2

from donna.domain.ids import ArtifactId, ArtifactLocalId, FullArtifactId, FullArtifactLocalId, WorldId
from donna.machine.templates import DirectiveKind, DirectiveSectionMeta, load_directive_section


class RenderMode(enum.Enum):
    """Modes for rendering artifacts.

    Donna could render artifacts for different purposes, for example:

    - to be displayed to the agent when Donna is used via CLI
    - TODO: to be displayed to the agent when Donna is used as an agent tool
    - TODO: to be displayed to the agent when Donna is used as an MCP server
    - to be used for analysis by Donna itself

    In each mode Donna can produce different outputs.

    For example, it can output CLI commands in CLI mode, tool specifications in tool mode,
    special markup in analyze mode, etc.
    """

    cli = "cli"
    analysis = "analysis"


_render_mode: ContextVar[RenderMode | None] = ContextVar("render_mode", default=None)


@contextmanager
def render_mode(mode: RenderMode) -> Iterator[None]:
    token = _render_mode.set(mode)

    try:
        yield
    finally:
        _render_mode.reset(token)


def set_default_render_mode(mode: RenderMode) -> None:
    _render_mode.set(mode)


_ENVIRONMENT = None


def _known_world_ids() -> set[str]:
    from donna.world.config import config

    return {str(world.id) for world in config().worlds}


class DirectivePathBuilder:
    def __init__(self, parts: tuple[str, ...]) -> None:
        self._parts = parts

    def __getattr__(self, name: str) -> "DirectivePathBuilder":
        return DirectivePathBuilder(self._parts + (name,))

    def __getitem__(self, name: str) -> "DirectivePathBuilder":
        return DirectivePathBuilder(self._parts + (name,))

    @jinja2.pass_context
    def __call__(self, context: jinja2.runtime.Context, *argv: object, **kwargs: object) -> object:
        if len(self._parts) < 3:
            raise NotImplementedError("Directive path must include world, artifact, and directive parts.")

        world_id = WorldId(self._parts[0])
        artifact_id = ArtifactId(".".join(self._parts[1:-1]))
        local_id = ArtifactLocalId(self._parts[-1])

        directive_id = FullArtifactLocalId((world_id, artifact_id, local_id))
        section = load_directive_section(directive_id)
        directive = section.entity

        if directive is None:
            raise NotImplementedError(f"Directive '{directive_id}' is not available")

        if not isinstance(directive, DirectiveKind):
            raise NotImplementedError(f"Directive '{directive_id}' is not available")

        if not isinstance(section.meta, DirectiveSectionMeta):
            raise NotImplementedError(f"Directive '{directive_id}' does not have directive metadata")

        return directive(context, *argv, meta=section.meta, **kwargs)


class DirectivePathUndefined(jinja2.Undefined):
    def __getattr__(self, name: str) -> object:
        if not self._undefined_name or self._undefined_name not in _known_world_ids():
            return jinja2.Undefined(name=f"{self._undefined_name}.{name}")

        return DirectivePathBuilder((self._undefined_name, name))


def env() -> jinja2.Environment:
    global _ENVIRONMENT

    if _ENVIRONMENT is not None:
        return _ENVIRONMENT

    _ENVIRONMENT = jinja2.Environment(
        loader=None,
        # we render into markdown, not into HTML
        # i.e. before (possible) displaying in the browser,
        # the result of the jinja2 render will be rendered by markdown renderer
        # markdown renderer should take care of escaping
        autoescape=jinja2.select_autoescape(default=False, default_for_string=False),
        auto_reload=False,
        extensions=["jinja2.ext.do", "jinja2.ext.loopcontrols", "jinja2.ext.debug"],
        undefined=DirectivePathUndefined,
    )

    return _ENVIRONMENT


def render(artifact_id: FullArtifactId, template: str) -> str:
    context = {"render_mode": _render_mode.get(), "artifact_id": artifact_id}

    template_obj = env().from_string(template)
    return template_obj.render(**context)
