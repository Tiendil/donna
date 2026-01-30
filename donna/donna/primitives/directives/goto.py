from typing import Any

from jinja2.runtime import Context

from donna.core import errors as core_errors
from donna.core.errors import ErrorsList
from donna.core.result import Err, Ok, Result
from donna.domain.ids import FullArtifactSectionId
from donna.machine.templates import Directive, PreparedDirectiveResult
from donna.protocol.modes import mode


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
        context: Context,
        *argv: Any,
    ) -> PreparedDirectiveResult:
        if argv is None or len(argv) != 1:
            return Err([GoToInvalidArguments(provided_count=0 if argv is None else len(argv))])

        artifact_id = context["artifact_id"]

        next_operation_id = artifact_id.to_full_local(argv[0])

        return Ok((next_operation_id,))

    def render_view(self, context: Context, next_operation_id: FullArtifactSectionId) -> Result[Any, ErrorsList]:
        protocol = mode().value
        return Ok(f"donna -p {protocol} sessions action-request-completed <action-request-id> '{next_operation_id}'")

    def render_analyze(self, context: Context, next_operation_id: FullArtifactSectionId) -> Result[Any, ErrorsList]:
        return Ok(f"$$donna {self.analyze_id} {next_operation_id.local_id} donna$$")
