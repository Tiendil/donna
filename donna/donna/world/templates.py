import enum
import importlib
import importlib.util
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterator

import jinja2

from donna.domain.ids import FullArtifactId
from donna.machine.templates import DirectiveKind


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


def _is_importable_module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


class DirectivePathBuilder:
    def __init__(self, parts: tuple[str, ...]) -> None:
        self._parts = parts

    def __getattr__(self, name: str) -> "DirectivePathBuilder":
        return DirectivePathBuilder(self._parts + (name,))

    def __getitem__(self, name: str) -> "DirectivePathBuilder":
        return DirectivePathBuilder(self._parts + (name,))

    @jinja2.pass_context
    def __call__(self, context: jinja2.runtime.Context, *argv: object, **kwargs: object) -> object:
        if len(self._parts) < 2:
            raise NotImplementedError("Directive path must include module and directive parts.")

        module_path = ".".join(self._parts[:-1])
        directive_name = self._parts[-1]

        try:
            module = importlib.import_module(module_path)
        except ModuleNotFoundError as exc:
            raise NotImplementedError(f"Directive module '{module_path}' is not importable") from exc

        try:
            directive = getattr(module, directive_name)
        except AttributeError as exc:
            raise NotImplementedError(f"Directive '{module_path}.{directive_name}' is not available") from exc

        if not isinstance(directive, DirectiveKind):
            raise NotImplementedError(f"Directive '{module_path}.{directive_name}' is not a directive kind")

        return directive(context, *argv, **kwargs)


class DirectivePathUndefined(jinja2.Undefined):
    def __getattr__(self, name: str) -> object:
        if not self._undefined_name or not _is_importable_module(self._undefined_name):
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
