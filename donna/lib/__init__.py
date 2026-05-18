"""Shared instances for standard library kind definitions."""

from donna.primitives.artifacts import Workflow
from donna.primitives.directives import GoTo, TaskVariable
from donna.primitives.sections import FinishWorkflow, Output, RequestAction, RunScript, Text

workflow = Workflow()
text = Text()
request_action = RequestAction()
finish = FinishWorkflow()
output = Output()
run_script = RunScript()

goto = GoTo(analyze_id="goto")
task_variable = TaskVariable(analyze_id="task_variable")
