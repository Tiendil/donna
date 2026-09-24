import enum

from llm_tool_cli.core.errors import EnvironmentErrors
from llm_tool_cli.core.result import Err, Ok, Result

from donna.core import errors as core_errors
from donna.domain.artifact_ids import ArtifactId
from donna.machine.templates import Directive, PreparedDirectiveResult
from donna.machine.templates_context import DirectiveContext
from donna.workspaces import config as workspace_config
from donna.workspaces.paths import normalize_project_path, resolve_project_path


class PathRenderMode(enum.StrEnum):
    project = "project"
    absolute = "absolute"


class EnvironmentError(core_errors.EnvironmentError):
    cell_kind: str = "directive_error"


class PathInvalidArguments(EnvironmentError):
    code: str = "donna.directives.path.invalid_arguments"
    message: str = (
        "Path directive requires exactly one path argument and an optional mode keyword "
        "(got {error.provided_count} positional arguments)."
    )
    ways_to_fix: list[str] = ['Use `donna.lib.path("<path>")` or `donna.lib.path("<path>", mode="absolute")`.']
    provided_count: int


class PathInvalidKeywordArguments(EnvironmentError):
    code: str = "donna.directives.path.invalid_keyword_arguments"
    message: str = "Path directive received unsupported keyword arguments: {error.keywords}."
    ways_to_fix: list[str] = ['Use only the optional `mode` keyword: `mode="project"` or `mode="absolute"`.']
    keywords: list[str]


class PathInvalidMode(EnvironmentError):
    code: str = "donna.directives.path.invalid_mode"
    message: str = "Path directive mode must be `project` or `absolute`, got `{error.mode}`."
    ways_to_fix: list[str] = ['Use `mode="project"` or `mode="absolute"`.']
    mode: str


class PathArtifactContextMissing(EnvironmentError):
    code: str = "donna.directives.path.artifact_context_missing"
    message: str = "Path directive requires the current artifact id to resolve workflow-relative paths."
    ways_to_fix: list[str] = ["Render the directive inside a workflow artifact."]


class PathNotProjectPath(EnvironmentError):
    code: str = "donna.directives.path.not_project_path"
    message: str = "Path directive could not normalize `{error.path}` to a project path inside the project root."
    ways_to_fix: list[str] = ["Use a root-anchored path or a path that resolves inside the Donna project root."]
    path: str


class Path(Directive):
    def _prepare_arguments(
        self,
        context: DirectiveContext,
        *argv: object,
        **kwargs: object,
    ) -> PreparedDirectiveResult:
        if argv is None or len(argv) != 1:
            return Err([PathInvalidArguments(provided_count=0 if argv is None else len(argv))])

        extra_keywords = sorted(set(kwargs) - {"mode"})
        if extra_keywords:
            return Err([PathInvalidKeywordArguments(keywords=extra_keywords)])

        try:
            mode = PathRenderMode(str(kwargs.get("mode", PathRenderMode.project)))
        except ValueError:
            return Err([PathInvalidMode(mode=str(kwargs.get("mode")))])

        raw_artifact_id = context.get("artifact_id")
        if not isinstance(raw_artifact_id, str):
            return Err([PathArtifactContextMissing()])

        return Ok((str(argv[0]), mode, ArtifactId(raw_artifact_id)))

    def render_view(self, context: DirectiveContext, *argv: object) -> Result[object, EnvironmentErrors]:
        raw_path = str(argv[0])
        mode: PathRenderMode = argv[1]  # type: ignore[assignment]
        artifact_id: ArtifactId = argv[2]  # type: ignore[assignment]
        project_root = workspace_config.project_dir()

        normalized = normalize_project_path(raw_path, project_root, relative_to=artifact_id)

        if normalized is None:
            return Err([PathNotProjectPath(path=raw_path)])

        if mode == PathRenderMode.project:
            return Ok(normalized)

        absolute = resolve_project_path(normalized, project_root)

        if absolute is None:
            return Err([PathNotProjectPath(path=raw_path)])

        return Ok(str(absolute))

    def render_analyze(self, context: DirectiveContext, *argv: object) -> Result[object, EnvironmentErrors]:
        return self.render_view(context, *argv)
