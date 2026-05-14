"""Shared instances for standard library kind definitions."""

from donna.primitives.artifacts.workflow import Workflow
from donna.primitives.directives.goto import GoTo
from donna.primitives.directives.task_variable import TaskVariable
from donna.primitives.sections.finish_workflow import FinishWorkflow
from donna.primitives.sections.output import Output
from donna.primitives.sections.request_action import RequestAction
from donna.primitives.sections.run_script import RunScript
from donna.primitives.sections.text import Text

workflow = Workflow()
text = Text()
request_action = RequestAction()
finish = FinishWorkflow()
output = Output()
run_script = RunScript()

goto = GoTo(analyze_id="goto")
task_variable = TaskVariable(analyze_id="task_variable")
