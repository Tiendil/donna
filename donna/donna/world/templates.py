import enum
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterator

import jinja2

from donna.domain.ids import FullArtifactId


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


def env() -> jinja2.Environment:
    from donna.world.primitives_register import register

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
    )

    for renderer in register().renderers.values():
        _ENVIRONMENT.globals[renderer.id] = renderer

    return _ENVIRONMENT


def render(artifact_id: FullArtifactId, template: str) -> str:
    context = {"render_mode": _render_mode.get(), "artifact_id": artifact_id}

    template_obj = env().from_string(template)
    return template_obj.render(**context)
