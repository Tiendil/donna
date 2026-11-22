import re
import stat

from llm_tool_cli.config.project import project_config
from llm_tool_cli.core.result import Err, Ok, Result, unwrap_to_error
from llm_tool_cli.paths import PathInput, ProjectPathId, resolve_project_path

from donna.core import errors as core_errors
from donna.domain.artifact_ids import ArtifactId
from donna.machine.templates import Directive, PreparedDirectiveResult
from donna.machine.templates_context import DirectiveContext
from donna.workspaces.paths import normalize_project_path


class EnvironmentError(core_errors.EnvironmentError):
    """Base class for directive environment errors."""


class IncludeInvalidArguments(EnvironmentError):
    code: str = "donna.directives.include.invalid_arguments"
    message: str = "Include directive requires exactly one string path argument."
    ways_to_fix: list[str] = ['Use `donna.lib.include("<path>")`.']


class IncludeArtifactContextMissing(EnvironmentError):
    code: str = "donna.directives.include.artifact_context_missing"
    message: str = "Include directive requires the current artifact id to resolve workflow-relative paths."
    ways_to_fix: list[str] = ["Render the directive inside a workflow artifact."]


class IncludeFileUnreadable(EnvironmentError):
    code: str = "donna.directives.include.file_unreadable"
    message: str = "Could not include `{error.path}` in `{error.artifact_id}`. {error.reason}"
    ways_to_fix: list[str] = ["Use the path of a readable UTF-8 text file in the project."]
    path: ProjectPathId
    artifact_id: ArtifactId
    reason: str


class Include(Directive):
    @unwrap_to_error
    def _prepare_arguments(
        self,
        context: DirectiveContext,
        *argv: object,
        **kwargs: object,
    ) -> PreparedDirectiveResult:
        if len(argv) != 1 or kwargs or not isinstance(argv[0], str):
            return Err([IncludeInvalidArguments()])

        raw_artifact_id = context.get("artifact_id")
        if not isinstance(raw_artifact_id, str):
            return Err([IncludeArtifactContextMissing()])

        artifact_id = ArtifactId(raw_artifact_id)
        project_root = project_config.get().project_dir
        path = normalize_project_path(argv[0], PathInput(project_root), relative_to=artifact_id).unwrap()
        return Ok((path, artifact_id))

    @unwrap_to_error
    def render_view(self, context: DirectiveContext, *argv: object) -> Result[object]:
        path: ProjectPathId = argv[0]  # type: ignore[assignment]
        artifact_id: ArtifactId = argv[1]  # type: ignore[assignment]
        file_path = resolve_project_path(path, project_config.get().project_dir).unwrap()

        try:
            if not stat.S_ISREG(file_path.stat().st_mode):
                return Err(
                    [IncludeFileUnreadable(path=path, artifact_id=artifact_id, reason="Expected a regular file.")]
                )

            return Ok(file_path.read_bytes().decode("utf-8"))
        except (OSError, UnicodeError) as exc:
            return Err([IncludeFileUnreadable(path=path, artifact_id=artifact_id, reason=str(exc)).with_cause(exc)])

    def render_analyze(self, context: DirectiveContext, *argv: object) -> Result[object]:
        path: ProjectPathId = argv[0]  # type: ignore[assignment]
        # Keep a path containing marker delimiters or line breaks inside a single analysis marker.
        escaped = re.sub(r"[\x00-\x1f\x7f-\x9f\u2028\u2029$\\]", lambda match: f"\\u{ord(match[0]):04x}", path)
        return super().render_analyze(context, escaped)
