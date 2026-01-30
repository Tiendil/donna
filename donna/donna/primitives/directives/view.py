from typing import Any

from jinja2.runtime import Context

from donna.core import errors as core_errors
from donna.core.errors import ErrorsList
from donna.core.result import Err, Ok, Result
from donna.domain.ids import FullArtifactId
from donna.machine.templates import Directive, PreparedDirectiveResult
from donna.protocol.modes import mode


class EnvironmentError(core_errors.EnvironmentError):
    cell_kind: str = "directive_error"


class ViewInvalidArguments(EnvironmentError):
    code: str = "donna.directives.view.invalid_arguments"
    message: str = "View directive requires exactly one argument: specification_id (got {error.provided_count})."
    ways_to_fix: list[str] = ["Provide exactly one argument: specification_id."]
    provided_count: int


class View(Directive):
    def _prepare_arguments(
        self,
        context: Context,
        *argv: Any,
    ) -> PreparedDirectiveResult:
        if argv is None or len(argv) != 1:
            return Err([ViewInvalidArguments(provided_count=0 if argv is None else len(argv))])

        artifact_id_result = FullArtifactId.parse(str(argv[0]))
        errors = artifact_id_result.err()
        if errors is not None:
            return Err(errors)

        artifact_id = artifact_id_result.ok()
        assert artifact_id is not None

        return Ok((artifact_id,))

    def render_view(self, context: Context, specification_id: FullArtifactId) -> Result[Any, ErrorsList]:
        protocol = mode().value
        return Ok(f"donna -p {protocol} artifacts view '{specification_id}'")
