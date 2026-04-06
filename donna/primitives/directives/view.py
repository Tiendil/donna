from typing import Any

from jinja2.runtime import Context

from donna.core import errors as core_errors
from donna.core.errors import ErrorsList
from donna.core.result import Err, Ok, Result, unwrap_to_error
from donna.domain import errors as domain_errors
from donna.domain.artifact_ids import ArtifactIdPattern, normalize_path
from donna.machine.artifacts import ArtifactPredicate
from donna.machine.templates import Directive, PreparedDirectiveResult
from donna.workspaces import config as workspace_config


class EnvironmentError(core_errors.EnvironmentError):
    cell_kind: str = "directive_error"


class ViewInvalidArguments(EnvironmentError):
    code: str = "donna.directives.view.invalid_arguments"
    message: str = (
        "View directive requires exactly one positional argument: artifact_id_pattern (got {error.provided_count})."
    )
    ways_to_fix: list[str] = ["Provide exactly one argument: artifact_id_pattern."]
    provided_count: int


class ViewInvalidKeyword(EnvironmentError):
    code: str = "donna.directives.view.invalid_keyword"
    message: str = "View directive accepts only the `predicate` keyword argument (got {error.keyword})."
    ways_to_fix: list[str] = ["Remove unsupported keyword arguments."]
    keyword: str


class ViewInvalidPredicate(EnvironmentError):
    code: str = "donna.directives.view.invalid_predicate"
    message: str = "View directive `predicate` must be a string."
    ways_to_fix: list[str] = ["Provide predicate as a string, e.g. predicate='section.kind == \"...\"'."]


class View(Directive):
    @unwrap_to_error
    def _prepare_arguments(  # noqa: CCR001
        self,
        context: Context,
        *argv: Any,
        **kwargs: Any,
    ) -> PreparedDirectiveResult:
        if argv is None or len(argv) != 1:
            return Err([ViewInvalidArguments(provided_count=0 if argv is None else len(argv))])

        for keyword in kwargs:
            if keyword != "predicate":
                return Err([ViewInvalidKeyword(keyword=keyword)])

        artifact_pattern_text = str(argv[0])
        normalized = normalize_path(artifact_pattern_text, relative_to=context["artifact_id"], allow_wildcards=True)
        if normalized is None:
            return Err(
                [domain_errors.InvalidIdPattern(id_type=ArtifactIdPattern.__name__, value=artifact_pattern_text)]
            )

        artifact_pattern = ArtifactIdPattern.parse(str(normalized)).unwrap()

        predicate = kwargs.get("predicate")
        if predicate is None:
            parsed_predicate: ArtifactPredicate | None = None
        elif isinstance(predicate, str):
            parsed_predicate = ArtifactPredicate.parse(predicate).unwrap()
        else:
            return Err([ViewInvalidPredicate()])

        return Ok((artifact_pattern, parsed_predicate))

    def render_view(
        self, context: Context, artifact_pattern: ArtifactIdPattern, predicate: ArtifactPredicate | None
    ) -> Result[Any, ErrorsList]:
        protocol = workspace_config.protocol().value
        root_dir = workspace_config.project_dir()
        predicate_suffix = ""
        if predicate is not None:
            escaped = predicate.source.replace("'", "'\"'\"'")
            predicate_suffix = f" --predicate '{escaped}'"
        return Ok(
            f"{artifact_pattern} (donna -p {protocol} -r '{root_dir}' "
            f"artifacts view '{artifact_pattern}'{predicate_suffix})"
        )

    def render_analyze(
        self, context: Context, artifact_pattern: ArtifactIdPattern, predicate: ArtifactPredicate | None
    ) -> Result[Any, ErrorsList]:
        if predicate is None:
            return Ok(f"$$donna {self.analyze_id} {artifact_pattern} donna$$")

        return Ok(f"$$donna {self.analyze_id} {artifact_pattern} predicate={predicate.source!r} donna$$")
