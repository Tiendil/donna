from __future__ import annotations

import importlib
import importlib.util
from collections.abc import Callable, Sequence
from pathlib import PurePosixPath
from typing import TYPE_CHECKING, cast

import jinja2
from llm_tool_cli.config.project import project_config
from llm_tool_cli.core import errors as llm_tool_errors
from llm_tool_cli.core.errors import EnvironmentErrors, EnvironmentErrorsProxy
from llm_tool_cli.core.result import Err, Ok, Result
from llm_tool_cli.paths import ProjectRootPath, RelativeProjectPath, normalize_project_path_id, project_path_parts

from donna.domain.artifact_ids import ArtifactId
from donna.machine.templates import Directive
from donna.machine.templates_context import DirectiveContext
from donna.workspaces import config as workspace_config
from donna.workspaces import errors as world_errors

if TYPE_CHECKING:
    from donna.machine import ArtifactRenderContext


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
    def __call__(self, context: DirectiveContext, *argv: object, **kwargs: object) -> object:  # noqa: CCR001
        raw_artifact_id = context.get("artifact_id")
        artifact_id = cast(ArtifactId | None, raw_artifact_id if isinstance(raw_artifact_id, str) else None)
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
        except llm_tool_errors.InternalError:
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
            result = directive.apply_directive(context, *argv, **kwargs)
        except llm_tool_errors.InternalError:
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


class _ProjectTemplateLoader(jinja2.BaseLoader):
    # Jinja searches template_dirs in order for a name like "steps.md". Donna treats
    # "@/templates/steps.md" as an exact path from the project root within a configured
    # template directory. Jinja's ChoiceLoader tries the next loader when a template
    # is missing, so it could resolve a missing @/ path under a directory literally
    # named @ in one of the search roots.
    def __init__(self, project_dir: ProjectRootPath, template_dirs: Sequence[RelativeProjectPath]) -> None:
        self._template_dirs = template_dirs
        self._files = jinja2.FileSystemLoader([project_dir / directory for directory in template_dirs])
        self._exact = jinja2.FileSystemLoader(project_dir)

    def get_source(
        self, environment: jinja2.Environment, template: str
    ) -> tuple[str, str | None, Callable[[], bool] | None]:
        if not template.startswith("@/"):
            return self._files.get_source(environment, template)

        path_id = normalize_project_path_id(template).ok()
        if path_id is None or path_id != template:
            raise jinja2.TemplateNotFound(template)

        relative_path = PurePosixPath(*project_path_parts(path_id))
        parent = relative_path.parent
        if not any(parent.is_relative_to(directory.as_posix()) for directory in self._template_dirs):
            raise jinja2.TemplateNotFound(template)

        try:
            return self._exact.get_source(environment, relative_path.as_posix())
        except jinja2.TemplateNotFound as exc:
            raise jinja2.TemplateNotFound(template) from exc


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
        autoescape=jinja2.select_autoescape(enabled_extensions=(), default_for_string=False, default=False),
        auto_reload=False,
        extensions=["jinja2.ext.do", "jinja2.ext.loopcontrols", "jinja2.ext.debug"],
        undefined=DirectivePathUndefined,
    )

    return _ENVIRONMENT


def render_environment() -> jinja2.Environment:
    template_dirs = workspace_config.config.get().template_dirs
    loader = _ProjectTemplateLoader(project_config.get().project_dir, template_dirs)
    return env().overlay(loader=loader)


def render(  # noqa: CCR001
    artifact_id: ArtifactId,
    template: str,
    render_context: "ArtifactRenderContext",
    *,
    environment: jinja2.Environment | None = None,
) -> Result[str]:
    # The Markdown parser renders in view mode for previews or execute mode for runs.
    # It renders again in analysis mode to discover goto transitions. It passes one
    # environment to both calls so Jinja can reuse compiled includes.
    if environment is None:
        environment = render_environment()

    context: dict[str, object] = {"render_mode": render_context.primary_mode, "artifact_id": artifact_id}

    if render_context.current_task is not None:
        context["current_task"] = render_context.current_task

    if render_context.current_work_unit is not None:
        context["current_work_unit"] = render_context.current_work_unit

    try:
        template_obj = environment.from_string(template)
        return Ok(template_obj.render(**context))
    except EnvironmentErrorsProxy as exc:
        return Err(cast(EnvironmentErrors, exc.details["errors"]))
    except jinja2.TemplateNotFound as exc:
        name = exc.name if isinstance(exc.name, str) else str(exc)
        return Err([world_errors.TemplateNotFound(artifact_id=artifact_id, template=name)])
    except jinja2.TemplateSyntaxError as exc:
        reason = f"{exc.filename or artifact_id}:{exc.lineno}: {exc.message}"
        return Err([world_errors.TemplateRenderFailed(artifact_id=artifact_id, reason=reason)])
    except (jinja2.TemplateError, OSError, RecursionError, UnicodeError) as exc:
        return Err([world_errors.TemplateRenderFailed(artifact_id=artifact_id, reason=str(exc))])
