"""Shared instances for standard library kind definitions."""

from donna.primitives.artifacts.specification import Specification, Text
from donna.primitives.artifacts.workflow import Workflow
from donna.primitives.directives.goto import GoTo
from donna.primitives.directives.list import List
from donna.primitives.directives.task_variable import TaskVariable
from donna.primitives.directives.view import View
from donna.primitives.operations.finish_workflow import FinishWorkflow
from donna.primitives.operations.output import Output
from donna.primitives.operations.request_action import RequestAction
from donna.primitives.operations.run_script import RunScript

specification = Specification()
workflow = Workflow()
text = Text()
request_action = RequestAction()
finish = FinishWorkflow()
output = Output()
run_script = RunScript()

view = View(analyze_id="view")
list = List(analyze_id="list")
goto = GoTo(analyze_id="goto")
task_variable = TaskVariable(analyze_id="task_variable")
