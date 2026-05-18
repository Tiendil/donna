from typing import cast

from donna.core import errors as core_errors
from donna.core.errors import ErrorsList
from donna.core.result import Err, Ok, Result
from donna.domain.artifact_ids import ArtifactId, ArtifactSectionId, artifact_section_id, split_artifact_section_id
from donna.machine.templates import Directive, PreparedDirectiveResult
from donna.machine.templates_context import DirectiveContext
from donna.workspaces import config as workspace_config


class EnvironmentError(core_errors.EnvironmentError):
    cell_kind: str = "directive_error"


class GoToInvalidArguments(EnvironmentError):
    code: str = "donna.directives.goto.invalid_arguments"
    message: str = "GoTo directive requires exactly one argument: next_operation_id (got {error.provided_count})."
    ways_to_fix: list[str] = ["Provide exactly one argument: next_operation_id."]
    provided_count: int


class GoTo(Directive):
    def _prepare_arguments(
        self,
        context: DirectiveContext,
        *argv: object,
        **kwargs: object,
    ) -> PreparedDirectiveResult:
        if argv is None or len(argv) != 1:
            return Err([GoToInvalidArguments(provided_count=0 if argv is None else len(argv))])

        artifact_id = cast(ArtifactId, context["artifact_id"])

        next_operation_id = artifact_section_id(artifact_id, str(argv[0]))

        return Ok((next_operation_id,))

    def render_view(self, context: DirectiveContext, *argv: object) -> Result[object, ErrorsList]:
        next_operation_id = cast(ArtifactSectionId, argv[0])
        protocol = workspace_config.protocol().value
        config_path = workspace_config.config_path()
        return Ok(
            f"donna -p {protocol} --config '{config_path}' "
            f"complete-action-request <action-request-id> '{next_operation_id}'"
        )

    def render_analyze(self, context: DirectiveContext, *argv: object) -> Result[object, ErrorsList]:
        next_operation_id = cast(ArtifactSectionId, argv[0])
        parts = split_artifact_section_id(next_operation_id)
        assert parts is not None
        return Ok(f"$$donna {self.analyze_id} {parts.section_id} donna$$")
