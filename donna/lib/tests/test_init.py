import donna.lib as lib
from donna.primitives.artifacts import Workflow
from donna.primitives.directives import GoTo, TaskVariable
from donna.primitives.sections import FinishWorkflow, Output, RequestAction, RunScript, Text


class TestPrimitiveInitialization:
    def test_section_and_artifact_primitives_are_initialized(self) -> None:
        assert isinstance(lib.workflow, Workflow)
        assert isinstance(lib.text, Text)
        assert isinstance(lib.request_action, RequestAction)
        assert isinstance(lib.finish, FinishWorkflow)
        assert isinstance(lib.output, Output)
        assert isinstance(lib.run_script, RunScript)

    def test_directive_primitives_are_initialized_with_analyze_ids(self) -> None:
        assert isinstance(lib.goto, GoTo)
        assert lib.goto.analyze_id == "goto"
        assert isinstance(lib.task_variable, TaskVariable)
        assert lib.task_variable.analyze_id == "task_variable"
