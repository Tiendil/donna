from typing import Any

from jinja2.runtime import Context

from donna.core import errors as core_errors
from donna.core.errors import ErrorsList
from donna.core.result import Err, Ok, Result
from donna.domain.ids import FullArtifactIdPattern
from donna.machine.templates import Directive, PreparedDirectiveResult
from donna.protocol.modes import mode
from donna.workspaces import config as workspace_config


class EnvironmentError(core_errors.EnvironmentError):
    cell_kind: str = "directive_error"


class ListInvalidArguments(EnvironmentError):
    code: str = "donna.directives.list.invalid_arguments"
    message: str = (
        "List directive requires exactly one positional argument: artifact_id_pattern (got {error.provided_count})."
    )
    ways_to_fix: list[str] = ["Provide exactly one argument: artifact_id_pattern."]
    provided_count: int


class ListInvalidKeyword(EnvironmentError):
    code: str = "donna.directives.list.invalid_keyword"
    message: str = "List directive accepts only the `tags` keyword argument (got {error.keyword})."
    ways_to_fix: list[str] = ["Remove unsupported keyword arguments."]
    keyword: str


class ListInvalidTags(EnvironmentError):
    code: str = "donna.directives.list.invalid_tags"
    message: str = "List directive `tags` must be a list of strings."
    ways_to_fix: list[str] = ["Provide tags as a list of strings, e.g. tags=['tag1', 'tag2']."]


class List(Directive):
    def _prepare_arguments(  # noqa: CCR001
        self,
        context: Context,
        *argv: Any,
        **kwargs: Any,
    ) -> PreparedDirectiveResult:
        if argv is None or len(argv) != 1:
            return Err([ListInvalidArguments(provided_count=0 if argv is None else len(argv))])

        for keyword in kwargs:
            if keyword != "tags":
                return Err([ListInvalidKeyword(keyword=keyword)])

        artifact_pattern_result = FullArtifactIdPattern.parse(str(argv[0]))
        errors = artifact_pattern_result.err()
        if errors is not None:
            return Err(errors)

        artifact_pattern = artifact_pattern_result.ok()
        assert artifact_pattern is not None

        tags = kwargs.get("tags")
        if tags is None:
            tags_list: list[str] = []
        elif isinstance(tags, (list, tuple, set)):
            tags_list = [str(tag) for tag in tags]
        else:
            return Err([ListInvalidTags()])

        return Ok((artifact_pattern, tags_list))

    def render_view(
        self, context: Context, artifact_pattern: FullArtifactIdPattern, tags: list[str]
    ) -> Result[Any, ErrorsList]:
        protocol = mode().value
        root_dir = workspace_config.project_dir()
        tags_args = " ".join(f"--tag '{tag}'" for tag in tags)
        tag_suffix = f" {tags_args}" if tags_args else ""
        return Ok(
            f"{artifact_pattern} (donna -p {protocol} -r '{root_dir}' "
            f"artifacts list '{artifact_pattern}'{tag_suffix})"
        )

    def render_analyze(
        self, context: Context, artifact_pattern: FullArtifactIdPattern, tags: list[str]
    ) -> Result[Any, ErrorsList]:
        if not tags:
            return Ok(f"$$donna {self.analyze_id} {artifact_pattern} donna$$")

        tags_marker = ",".join(tags)
        return Ok(f"$$donna {self.analyze_id} {artifact_pattern} tags={tags_marker} donna$$")
