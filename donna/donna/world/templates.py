from __future__ import annotations

import enum
import importlib
import importlib.util
from typing import TYPE_CHECKING

import jinja2

from donna.core import errors as core_errors
from donna.core.errors import EnvironmentErrorsProxy, ErrorsList
from donna.core.result import Err, Ok, Result
from donna.domain.ids import FullArtifactId
from donna.machine.templates import Directive
from donna.world import errors as world_errors

if TYPE_CHECKING:
    from donna.world.artifacts import ArtifactRenderContext


class RenderMode(enum.Enum):
    """Modes for rendering artifacts.

    Donna could render artifacts for different purposes, for example:

    - to be displayed to the agent when Donna is used via CLI
    - TODO: to be displayed to the agent when Donna is used as an agent tool
    - TODO: to be displayed to the agent when Donna is used as an MCP server
    - to be used for analysis by Donna itself

    In each mode Donna can produce different outputs.

    For example, it can output CLI commands in view/execute mode, tool specifications in tool mode,
    special markup in analyze mode, etc.
    """

    view = "view"
    execute = "execute"
    analysis = "analysis"


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
    def __call__(self, context: jinja2.runtime.Context, *argv: object) -> object:  # noqa: CCR001
        artifact_id = context.get("artifact_id")
        directive_path = ".".join(self._parts)
        if len(self._parts) < 2:
            raise EnvironmentErrorsProxy(
                [world_errors.DirectivePathIncomplete(path=directive_path, artifact_id=artifact_id)]
            )

        module_path = ".".join(self._parts[:-1])
        directive_name = self._parts[-1]

        try:
            module = importlib.import_module(module_path)
        except ModuleNotFoundError as exc:
            raise EnvironmentErrorsProxy(
                [world_errors.DirectiveModuleNotImportable(module_path=module_path, artifact_id=artifact_id)]
            ) from exc
        except core_errors.InternalError:
            raise
        except Exception as exc:
            raise EnvironmentErrorsProxy(
                [
                    world_errors.DirectiveUnexpectedError(
                        directive_path=directive_path,
                        details=str(exc),
                        artifact_id=artifact_id,
                    )
                ]
            ) from exc

        try:
            directive = getattr(module, directive_name)
        except AttributeError as exc:
            raise EnvironmentErrorsProxy(
                [
                    world_errors.DirectiveNotAvailable(
                        module_path=module_path,
                        directive_name=directive_name,
                        artifact_id=artifact_id,
                    )
                ]
            ) from exc

        if not isinstance(directive, Directive):
            raise EnvironmentErrorsProxy(
                [
                    world_errors.DirectiveNotDirective(
                        module_path=module_path,
                        directive_name=directive_name,
                        artifact_id=artifact_id,
                    )
                ]
            )

        try:
            result = directive.apply_directive(context, *argv)
        except EnvironmentErrorsProxy:
            raise
        except core_errors.InternalError:
            raise
        except Exception as exc:
            raise EnvironmentErrorsProxy(
                [
                    world_errors.DirectiveUnexpectedError(
                        directive_path=directive_path,
                        details=str(exc),
                        artifact_id=artifact_id,
                    )
                ]
            ) from exc

        if result.is_err():
            raise EnvironmentErrorsProxy(result.unwrap_err())

        return result.unwrap()


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


def render(
    artifact_id: FullArtifactId, template: str, render_context: "ArtifactRenderContext"
) -> Result[str, ErrorsList]:
    context = {"render_mode": render_context.primary_mode, "artifact_id": artifact_id}

    if render_context.current_task is not None:
        context["current_task"] = render_context.current_task

    if render_context.current_work_unit is not None:
        context["current_work_unit"] = render_context.current_work_unit

    try:
        template_obj = env().from_string(template)
        return Ok(template_obj.render(**context))
    except EnvironmentErrorsProxy as exc:
        return Err(exc.arguments["errors"])
