from donna.primitives.directives.task_variable import (
    TaskVariable,
    TaskVariableInvalidArguments,
    TaskVariableTaskContextMissing,
)
from donna.primitives.tests import make


class TestTaskVariable:
    def test_prepare_arguments__requires_one_argument(self) -> None:
        result = TaskVariable(analyze_id="task_variable")._prepare_arguments(make.template_context())

        assert result.is_err()
        error = result.unwrap_err()[0]
        assert isinstance(error, TaskVariableInvalidArguments)
        assert error.provided_count == 0

    def test_prepare_arguments__coerces_variable_name_to_string(self) -> None:
        result = TaskVariable(analyze_id="task_variable")._prepare_arguments(make.template_context(), 42)

        assert result.is_ok()
        assert result.unwrap() == ("42",)

    def test_render_view__describes_deferred_variable_substitution(self) -> None:
        result = TaskVariable(analyze_id="task_variable").render_view(make.template_context(), "answer")

        assert result.is_ok()
        content = result.unwrap()
        assert isinstance(content, str)
        assert "will place a value" in content
        assert "answer" in content

    def test_render_execute__returns_value_from_task_context_mapping(self) -> None:
        result = TaskVariable(analyze_id="task_variable").render_execute(
            make.template_context(task_context={"answer": 42}),
            "answer",
        )

        assert result.is_ok()
        assert result.unwrap() == 42

    def test_render_execute__returns_value_from_current_task_context(self) -> None:
        current_task = type("CurrentTask", (), {"context": {"answer": "yes"}})()

        result = TaskVariable(analyze_id="task_variable").render_execute(
            make.template_context(current_task=current_task),
            "answer",
        )

        assert result.is_ok()
        assert result.unwrap() == "yes"

    def test_render_execute__reports_missing_task_context(self) -> None:
        result = TaskVariable(analyze_id="task_variable").render_execute(make.template_context(), "answer")

        assert result.is_err()
        assert isinstance(result.unwrap_err()[0], TaskVariableTaskContextMissing)

    def test_render_execute__renders_warning_for_missing_variable(self) -> None:
        result = TaskVariable(analyze_id="task_variable").render_execute(
            make.template_context(task_context={}),
            "answer",
        )

        assert result.is_ok()
        content = result.unwrap()
        assert isinstance(content, str)
        assert "variable 'answer' does not found" in content
