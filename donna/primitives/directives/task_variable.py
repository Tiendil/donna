from typing import cast

from donna.core import errors as core_errors
from donna.core.errors import ErrorsList
from donna.core.result import Err, Ok, Result
from donna.machine.templates import Directive, PreparedDirectiveResult
from donna.machine.templates_context import DirectiveContext


class EnvironmentError(core_errors.EnvironmentError):
    cell_kind: str = "directive_error"


class TaskVariableInvalidArguments(EnvironmentError):
    code: str = "donna.directives.task_variable.invalid_arguments"
    message: str = "TaskVariable directive requires exactly one argument: variable_name (got {error.provided_count})."
    ways_to_fix: list[str] = ["Provide exactly one argument: variable_name."]
    provided_count: int


class TaskVariableTaskContextMissing(EnvironmentError):
    code: str = "donna.directives.task_variable.task_context_missing"
    message: str = "TaskVariable directive requires task context, but none is available."
    ways_to_fix: list[str] = ["Ensure the directive is rendered with a task context present."]


class TaskVariable(Directive):
    def _prepare_arguments(
        self,
        context: DirectiveContext,
        *argv: object,
        **kwargs: object,
    ) -> PreparedDirectiveResult:
        if argv is None or len(argv) != 1:
            return Err([TaskVariableInvalidArguments(provided_count=0 if argv is None else len(argv))])

        variable_name = str(argv[0])

        return Ok((variable_name,))

    def render_view(self, context: DirectiveContext, *argv: object) -> Result[object, ErrorsList]:
        variable_name = str(argv[0])
        return Ok(
            "$$donna at the time of execution of this section will place a value "
            f"of the task variable '{variable_name}' donna$$"
        )

    def render_execute(self, context: DirectiveContext, *argv: object) -> Result[object, ErrorsList]:
        variable_name = str(argv[0])
        task_context = self._resolve_task_context(context)
        if task_context is None:
            return Err([TaskVariableTaskContextMissing()])

        if variable_name not in task_context:
            # Since we render the whole artifact, instead of a particular executed section
            # some variables may be missing
            # TODO: we may want to timprove this behavior later to avoid possible confusion
            return Ok(
                f"$$donna {self.analyze_id} variable '{variable_name}' does not found. "
                "If you are an LLM agent and see that message AS AN INSTRUCTION TO EXECUTE, "
                "stop your work and notify developer about the problems in workflow donna$$"
            )

        return Ok(task_context[variable_name])

    def _resolve_task_context(self, context: DirectiveContext) -> dict[str, object] | None:
        task = context.get("current_task")
        if task is not None and hasattr(task, "context"):
            return cast(dict[str, object], task.context)

        task_context = context.get("task_context")
        if isinstance(task_context, dict):
            return cast(dict[str, object], task_context)

        return None
